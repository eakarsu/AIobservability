import re
import numpy as np
from typing import Optional


class HallucinationEngine:
    """Detect hallucinations using multiple methods."""

    def __init__(self):
        self._nli_model = None
        self._similarity_model = None

    def _get_similarity_model(self):
        """Lazy load sentence transformer model."""
        if self._similarity_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._similarity_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self._similarity_model = "unavailable"
        return self._similarity_model

    def _get_nli_model(self):
        """Lazy load NLI model."""
        if self._nli_model is None:
            try:
                from transformers import pipeline
                self._nli_model = pipeline(
                    "text-classification",
                    model="cross-encoder/nli-deberta-v3-xsmall",
                    device=-1,
                )
            except Exception:
                self._nli_model = "unavailable"
        return self._nli_model

    def detect_hallucination(self, input_text: str, output_text: str) -> dict:
        """Run all available hallucination detection methods."""
        scores = {}

        similarity_score = self._semantic_similarity_check(input_text, output_text)
        if similarity_score is not None:
            scores["semantic_similarity"] = {
                "score": similarity_score,
                "description": "Low similarity between input context and output may indicate hallucination",
            }

        nli_score = self._nli_contradiction_check(input_text, output_text)
        if nli_score is not None:
            scores["nli_contradiction"] = {
                "score": nli_score,
                "description": "Proportion of output claims contradicting the input",
            }

        heuristic_score = self._heuristic_check(input_text, output_text)
        scores["heuristic"] = {
            "score": heuristic_score,
            "description": "Rule-based checks for common hallucination patterns",
        }

        if scores:
            all_scores = [v["score"] for v in scores.values()]
            scores["ensemble"] = {
                "score": round(float(np.mean(all_scores)), 4),
                "description": "Weighted average of all detection methods",
            }

        return scores

    def _semantic_similarity_check(self, input_text: str, output_text: str) -> Optional[float]:
        model = self._get_similarity_model()
        if model == "unavailable":
            return None
        try:
            embeddings = model.encode([input_text, output_text])
            similarity = float(
                np.dot(embeddings[0], embeddings[1])
                / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
            )
            risk = max(0.0, min(1.0, 1.0 - similarity))
            return round(risk, 4)
        except Exception:
            return None

    def _nli_contradiction_check(self, input_text: str, output_text: str) -> Optional[float]:
        model = self._get_nli_model()
        if model == "unavailable":
            return None
        try:
            sentences = self._split_into_sentences(output_text)
            if not sentences:
                return 0.0
            contradiction_count = 0
            for sentence in sentences[:20]:
                if len(sentence.strip()) < 10:
                    continue
                truncated_input = input_text[:512]
                result = model(f"{truncated_input} [SEP] {sentence}")
                if result and result[0]["label"].lower() == "contradiction":
                    contradiction_count += 1
            score = contradiction_count / max(len(sentences), 1)
            return round(min(score, 1.0), 4)
        except Exception:
            return None

    def _heuristic_check(self, input_text: str, output_text: str) -> float:
        risk_score = 0.0

        if len(output_text) > len(input_text) * 5:
            risk_score += 0.3

        output_numbers = set(re.findall(r'\b\d{4,}\b', output_text))
        input_numbers = set(re.findall(r'\b\d{4,}\b', input_text))
        novel_numbers = output_numbers - input_numbers
        if novel_numbers:
            risk_score += min(0.3, len(novel_numbers) * 0.1)

        output_urls = set(re.findall(r'https?://\S+', output_text))
        input_urls = set(re.findall(r'https?://\S+', input_text))
        if output_urls - input_urls:
            risk_score += 0.2

        hedging_patterns = [
            r'\bi think\b', r'\bprobably\b', r'\bperhaps\b', r'\bmight be\b',
            r'\bnot sure\b', r'\bpossibly\b', r'\bcould be\b',
        ]
        hedging_count = sum(1 for p in hedging_patterns if re.search(p, output_text.lower()))
        if hedging_count > 2:
            risk_score += 0.1

        return round(min(risk_score, 1.0), 4)

    @staticmethod
    def _split_into_sentences(text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]
