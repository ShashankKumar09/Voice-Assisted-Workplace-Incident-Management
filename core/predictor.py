"""
Reusable multi-task DeBERTa inference engine.

Loads only deployment assets:
- compact inference checkpoint
- local tokenizer
- label mappings
- relationship matrices
- frozen decision thresholds
"""

from __future__ import annotations

import gc
import json
import math
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from transformers import (
    AutoConfig,
    AutoModel,
    AutoTokenizer,
)


TASK_NAMES = [
    "nature",
    "body",
    "event",
    "source",
]

RELATIONSHIP_PAIRS = [
    ("nature", "body"),
    ("nature", "event"),
    ("nature", "source"),
    ("body", "event"),
    ("body", "source"),
    ("event", "source"),
]


class MultiTaskDeBERTa(nn.Module):
    """Shared DeBERTa encoder with four classification heads."""

    def __init__(
        self,
        encoder_config,
        number_of_classes: int = 50,
        dropout_rate: float = 0.25,
    ) -> None:

        super().__init__()

        self.encoder = AutoModel.from_config(
            encoder_config
        )

        hidden_size = int(
            encoder_config.hidden_size
        )

        self.dropout = nn.Dropout(
            float(dropout_rate)
        )

        self.nature_head = nn.Linear(
            hidden_size,
            number_of_classes,
        )

        self.body_head = nn.Linear(
            hidden_size,
            number_of_classes,
        )

        self.event_head = nn.Linear(
            hidden_size,
            number_of_classes,
        )

        self.source_head = nn.Linear(
            hidden_size,
            number_of_classes,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:

        encoder_outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        pooled_output = (
            encoder_outputs
            .last_hidden_state[:, 0]
        )

        pooled_output = self.dropout(
            pooled_output
        )

        return {
            "nature_logits":
                self.nature_head(
                    pooled_output
                ),

            "body_logits":
                self.body_head(
                    pooled_output
                ),

            "event_logits":
                self.event_head(
                    pooled_output
                ),

            "source_logits":
                self.source_head(
                    pooled_output
                ),
        }


def _load_json(path: Path) -> Dict[str, Any]:

    if not path.is_file():

        raise FileNotFoundError(
            f"Required configuration file was not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def _find_task_mapping(
    mapping_object: Dict[str, Any],
    task_name: str,
) -> Dict[str, Any]:

    for key, value in mapping_object.items():

        if str(key).strip().lower() == task_name.lower():

            return value

    raise KeyError(
        f"No label mapping found for task: {task_name}"
    )


def _standardize_id_to_label(
    task_mapping: Dict[str, Any],
) -> Dict[int, str]:

    if "id_to_label" in task_mapping:

        mapping = task_mapping[
            "id_to_label"
        ]

    else:

        mapping = task_mapping

    if not all(
        str(key).lstrip("-").isdigit()
        for key in mapping.keys()
    ):

        raise ValueError(
            "Unsupported label-mapping structure."
        )

    return {
        int(label_id): str(label_name)
        for label_id, label_name
        in mapping.items()
    }


class IncidentPredictor:
    """
    Deployment-safe incident classifier.

    One instance should be cached in Streamlit so the model is loaded once.
    """

    def __init__(
        self,
        application_root: str | Path,
        device: str = "auto",
    ) -> None:

        self.application_root = Path(
            application_root
        ).resolve()

        self.model_dir = (
            self.application_root
            / "models"
        )

        self.tokenizer_dir = (
            self.application_root
            / "tokenizer"
        )

        self.config_dir = (
            self.application_root
            / "config"
        )

        self.model_state_path = (
            self.model_dir
            / "multitask_deberta_inference_state.pt"
        )

        self.mapping_path = (
            self.config_dir
            / "label_mappings"
            / "top50_label_mappings.json"
        )

        self.relationship_path = (
            self.config_dir
            / "relationship_assets"
            / "pairwise_compatibility_matrices.npz"
        )

        self.decision_path = (
            self.config_dir
            / "model_configuration"
            / "frozen_decision_engine.json"
        )

        self.model_configuration_path = (
            self.config_dir
            / "model_configuration"
            / "multitask_model_configuration.json"
        )

        self.manifest_path = (
            self.config_dir
            / "deployment_manifest.json"
        )

        required_paths = [
            self.model_dir / "config.json",
            self.model_state_path,
            self.tokenizer_dir,
            self.mapping_path,
            self.relationship_path,
            self.decision_path,
            self.model_configuration_path,
            self.manifest_path,
        ]

        missing_paths = [
            str(path)
            for path in required_paths
            if not path.exists()
        ]

        if missing_paths:

            raise FileNotFoundError(
                "Deployment package is incomplete:\n"
                + "\n".join(
                    missing_paths
                )
            )

        if device == "auto":

            self.device = torch.device(
                "cuda:0"
                if torch.cuda.is_available()
                else "cpu"
            )

        else:

            requested_device = torch.device(
                device
            )

            if (
                requested_device.type == "cuda"
                and not torch.cuda.is_available()
            ):

                raise RuntimeError(
                    "CUDA was requested but is not available."
                )

            self.device = requested_device

        self.manifest = _load_json(
            self.manifest_path
        )

        self.decision_configuration = _load_json(
            self.decision_path
        )

        self.model_configuration = _load_json(
            self.model_configuration_path
        )

        self.task_names = [
            str(task).lower()
            for task
            in self.manifest["tasks"]
        ]

        if self.task_names != TASK_NAMES:

            raise ValueError(
                f"Unexpected task order: {self.task_names}"
            )

        self.number_of_classes = int(
            self.manifest[
                "classes_per_head"
            ]
        )

        self.maximum_sequence_length = int(
            self.manifest[
                "maximum_sequence_length"
            ]
        )

        self.dropout_rate = float(
            self.model_configuration.get(
                "dropout_rate",
                0.25,
            )
        )

        self.auto_fill_threshold = float(
            self.decision_configuration[
                "auto_fill_threshold"
            ]
        )

        self.suggest_review_threshold = float(
            self.decision_configuration[
                "suggest_review_threshold"
            ]
        )

        self.relationship_low_threshold = float(
            self.decision_configuration[
                "relationship_low_threshold"
            ]
        )

        self.relationship_high_threshold = float(
            self.decision_configuration[
                "relationship_high_threshold"
            ]
        )

        self.id_to_label = self._load_label_mappings()

        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.tokenizer_dir),
            use_fast=True,
            local_files_only=True,
        )

        encoder_config = AutoConfig.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
        )

        self.model = MultiTaskDeBERTa(
            encoder_config=encoder_config,
            number_of_classes=self.number_of_classes,
            dropout_rate=self.dropout_rate,
        )

        compact_asset = torch.load(
            self.model_state_path,
            map_location="cpu",
            weights_only=False,
        )

        if "model_state_dict" not in compact_asset:

            raise KeyError(
                "Compact model asset does not contain model_state_dict."
            )

        self.checkpoint_epoch = int(
            compact_asset.get(
                "checkpoint_epoch",
                -1,
            )
        )

        self.model.load_state_dict(
            compact_asset[
                "model_state_dict"
            ],
            strict=True,
        )

        self.model = (
            self.model
            .to(self.device)
            .float()
            .eval()
        )

        self.relationship_matrices = (
            self._load_relationship_matrices()
        )

        del compact_asset

        gc.collect()

        if torch.cuda.is_available():

            torch.cuda.empty_cache()

    def _load_label_mappings(
        self,
    ) -> Dict[str, Dict[int, str]]:

        raw_mappings = _load_json(
            self.mapping_path
        )

        standardized = {}

        for task_name in self.task_names:

            task_mapping = _find_task_mapping(
                raw_mappings,
                task_name,
            )

            id_to_label = _standardize_id_to_label(
                task_mapping
            )

            expected_ids = set(
                range(
                    self.number_of_classes
                )
            )

            if set(id_to_label.keys()) != expected_ids:

                raise ValueError(
                    f"{task_name.title()} label IDs are not exactly "
                    f"0–{self.number_of_classes - 1}."
                )

            standardized[
                task_name
            ] = id_to_label

        return standardized

    def _load_relationship_matrices(
        self,
    ) -> Dict[str, np.ndarray]:

        npz_file = np.load(
            self.relationship_path,
            allow_pickle=False,
        )

        matrices = {}

        for left_task, right_task in RELATIONSHIP_PAIRS:

            relationship_name = (
                f"{left_task}_{right_task}"
            )

            matrix_key = (
                f"{relationship_name}_compatibility"
            )

            if matrix_key not in npz_file.files:

                raise KeyError(
                    f"Relationship matrix is missing: {matrix_key}"
                )

            matrix = npz_file[
                matrix_key
            ].astype(
                np.float32
            )

            expected_shape = (
                self.number_of_classes,
                self.number_of_classes,
            )

            if matrix.shape != expected_shape:

                raise ValueError(
                    f"{matrix_key} has invalid shape: {matrix.shape}"
                )

            matrices[
                relationship_name
            ] = matrix

        return matrices

    def _decision_tier(
        self,
        overall_confidence: float,
    ) -> str:

        if (
            overall_confidence
            >= self.auto_fill_threshold
        ):

            return "Auto Fill"

        if (
            overall_confidence
            >= self.suggest_review_threshold
        ):

            return "Suggest Review"

        return "Manual Review"

    def _relationship_flag(
        self,
        relationship_score: float,
    ) -> str:

        if (
            relationship_score
            >= self.relationship_high_threshold
        ):

            return "High"

        if (
            relationship_score
            >= self.relationship_low_threshold
        ):

            return "Medium"

        return "Low"

    @staticmethod
    def historical_validation_label(
        flag: str,
    ) -> str:

        return {
            "High":
                "Strong Historical Support",

            "Medium":
                "Moderate Historical Support",

            "Low":
                "Limited Historical Support",
        }.get(
            flag,
            "Historical Support Not Available",
        )

    @torch.inference_mode()
    def predict(
        self,
        narrative: str,
        include_top_predictions: bool = True,
        top_k: int = 3,
    ) -> Dict[str, Any]:

        if narrative is None:

            raise ValueError(
                "Incident narrative cannot be None."
            )

        narrative = str(
            narrative
        ).strip()

        if not narrative:

            raise ValueError(
                "Incident narrative cannot be empty."
            )

        if len(narrative) < 10:

            raise ValueError(
                "Please provide a more descriptive incident narrative."
            )

        top_k = max(
            1,
            min(
                int(top_k),
                self.number_of_classes,
            ),
        )

        start_time = time.perf_counter()

        encoded = self.tokenizer(
            narrative,
            return_tensors="pt",
            truncation=True,
            max_length=self.maximum_sequence_length,
            padding=False,
        )

        token_count = int(
            encoded[
                "attention_mask"
            ].sum().item()
        )

        model_inputs = {
            key: value.to(
                self.device
            )
            for key, value
            in encoded.items()
            if key in {
                "input_ids",
                "attention_mask",
            }
        }

        with torch.amp.autocast(
            device_type=self.device.type,
            enabled=(
                self.device.type == "cuda"
            ),
        ):

            outputs = self.model(
                input_ids=model_inputs[
                    "input_ids"
                ],
                attention_mask=model_inputs[
                    "attention_mask"
                ],
            )

        predictions = {}
        predicted_ids = {}
        task_confidences = []

        for task_name in self.task_names:

            probabilities = F.softmax(
                outputs[
                    f"{task_name}_logits"
                ].float(),
                dim=1,
            )[0]

            confidence_tensor, label_tensor = torch.max(
                probabilities,
                dim=0,
            )

            label_id = int(
                label_tensor.item()
            )

            confidence = float(
                confidence_tensor.item()
            )

            predicted_ids[
                task_name
            ] = label_id

            task_confidences.append(
                confidence
            )

            task_result = {
                "label_id":
                    label_id,

                "label":
                    self.id_to_label[
                        task_name
                    ][label_id],

                "confidence":
                    confidence,

                "confidence_percent":
                    confidence * 100,
            }

            if include_top_predictions:

                top_values, top_indices = torch.topk(
                    probabilities,
                    k=top_k,
                )

                task_result[
                    "top_predictions"
                ] = [
                    {
                        "rank":
                            rank,

                        "label_id":
                            int(label_index),

                        "label":
                            self.id_to_label[
                                task_name
                            ][int(label_index)],

                        "confidence":
                            float(probability),

                        "confidence_percent":
                            float(probability) * 100,
                    }
                    for rank, (
                        probability,
                        label_index,
                    ) in enumerate(
                        zip(
                            top_values
                            .detach()
                            .cpu()
                            .tolist(),

                            top_indices
                            .detach()
                            .cpu()
                            .tolist(),
                        ),
                        start=1,
                    )
                ]

            predictions[
                task_name
            ] = task_result

        confidence_array = np.asarray(
            task_confidences,
            dtype=np.float64,
        )

        geometric_mean_confidence = float(
            np.exp(
                np.log(
                    np.clip(
                        confidence_array,
                        1e-12,
                        1.0,
                    )
                ).mean()
            )
        )

        pairwise_scores = {}

        for left_task, right_task in RELATIONSHIP_PAIRS:

            relationship_name = (
                f"{left_task}_{right_task}"
            )

            relationship_score = float(
                self.relationship_matrices[
                    relationship_name
                ][
                    predicted_ids[
                        left_task
                    ],
                    predicted_ids[
                        right_task
                    ],
                ]
            )

            readable_name = (
                f"{left_task.title()} ↔ "
                f"{right_task.title()}"
            )

            pairwise_scores[
                readable_name
            ] = relationship_score

        relationship_values = np.asarray(
            list(
                pairwise_scores.values()
            ),
            dtype=np.float64,
        )

        relationship_consistency_score = float(
            relationship_values.mean()
        )

        weakest_relationship = min(
            pairwise_scores,
            key=pairwise_scores.get,
        )

        weakest_relationship_score = float(
            pairwise_scores[
                weakest_relationship
            ]
        )

        relationship_flag = self._relationship_flag(
            relationship_consistency_score
        )

        historical_label = (
            self.historical_validation_label(
                relationship_flag
            )
        )

        if relationship_flag == "High":

            relationship_message = (
                "The predicted combination has strong historical support."
            )

        elif relationship_flag == "Medium":

            relationship_message = (
                "The predicted combination has moderate historical support."
            )

        else:

            relationship_message = (
                "The predicted combination has limited historical support."
            )

        inference_time_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        return {
            "status":
                "success",

            "narrative":
                narrative,

            "token_count":
                token_count,

            "maximum_token_length":
                self.maximum_sequence_length,

            "was_truncated":
                token_count
                >= self.maximum_sequence_length,

            "predictions":
                predictions,

            "incident_confidence": {
                "geometric_mean":
                    geometric_mean_confidence,

                "geometric_mean_percent":
                    geometric_mean_confidence * 100,

                "minimum_task_confidence":
                    float(
                        confidence_array.min()
                    ),

                "minimum_task_confidence_percent":
                    float(
                        confidence_array.min()
                    ) * 100,

                "mean_task_confidence":
                    float(
                        confidence_array.mean()
                    ),

                "mean_task_confidence_percent":
                    float(
                        confidence_array.mean()
                    ) * 100,
            },

            "decision": {
                "tier":
                    self._decision_tier(
                        geometric_mean_confidence
                    ),

                "auto_fill_threshold":
                    self.auto_fill_threshold,

                "suggest_review_threshold":
                    self.suggest_review_threshold,
            },

            "relationship_validation": {
                "consistency_score":
                    relationship_consistency_score,

                "flag":
                    relationship_flag,

                "historical_validation_status":
                    historical_label,

                "message":
                    relationship_message,

                "weakest_relationship":
                    weakest_relationship,

                "weakest_relationship_score":
                    weakest_relationship_score,

                "pairwise_scores":
                    pairwise_scores,
            },

            "model_information": {
                "model_name":
                    self.manifest[
                        "model_name"
                    ],

                "checkpoint_epoch":
                    self.checkpoint_epoch,

                "classes_per_head":
                    self.number_of_classes,

                "device":
                    str(
                        self.device
                    ),
            },

            "inference_time_ms":
                inference_time_ms,
        }


def load_predictor(
    application_root: str | Path,
    device: str = "auto",
) -> IncidentPredictor:
    """Convenience loader used by Streamlit."""

    return IncidentPredictor(
        application_root=application_root,
        device=device,
    )
