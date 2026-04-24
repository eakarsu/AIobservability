import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon


class DriftEngine:
    """Statistical drift detection using KS test, PSI, and Jensen-Shannon Divergence."""

    def detect_drift(self, reference: list[float], test: list[float]) -> dict:
        """Run all drift detection methods and return scores."""
        ref_arr = np.array(reference, dtype=float)
        test_arr = np.array(test, dtype=float)

        results = {}

        # Kolmogorov-Smirnov Test
        ks_stat, ks_pvalue = stats.ks_2samp(ref_arr, test_arr)
        results["ks_test"] = {
            "score": float(ks_stat),
            "p_value": float(ks_pvalue),
            "drifted": ks_pvalue < 0.05,
        }

        # Population Stability Index
        psi_score = self._calculate_psi(ref_arr, test_arr)
        results["psi"] = {
            "score": float(psi_score),
            "p_value": None,
            "drifted": psi_score > 0.1,
        }

        # Jensen-Shannon Divergence
        jsd_score = self._calculate_jsd(ref_arr, test_arr)
        results["jsd"] = {
            "score": float(jsd_score),
            "p_value": None,
            "drifted": jsd_score > 0.1,
        }

        return results

    def _calculate_psi(self, reference: np.ndarray, test: np.ndarray, bins: int = 10) -> float:
        """Calculate Population Stability Index."""
        breakpoints = np.percentile(reference, np.linspace(0, 100, bins + 1))
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf
        breakpoints = np.unique(breakpoints)
        if len(breakpoints) < 3:
            return 0.0

        ref_counts = np.histogram(reference, bins=breakpoints)[0]
        test_counts = np.histogram(test, bins=breakpoints)[0]

        epsilon = 1e-6
        ref_props = (ref_counts + epsilon) / (len(reference) + epsilon * len(ref_counts))
        test_props = (test_counts + epsilon) / (len(test) + epsilon * len(test_counts))

        psi = np.sum((test_props - ref_props) * np.log(test_props / ref_props))
        return max(0, psi)

    def _calculate_jsd(self, reference: np.ndarray, test: np.ndarray, bins: int = 50) -> float:
        """Calculate Jensen-Shannon Divergence."""
        all_data = np.concatenate([reference, test])
        bin_edges = np.histogram_bin_edges(all_data, bins=bins)

        ref_hist = np.histogram(reference, bins=bin_edges, density=True)[0]
        test_hist = np.histogram(test, bins=bin_edges, density=True)[0]

        ref_hist = ref_hist / (ref_hist.sum() + 1e-10)
        test_hist = test_hist / (test_hist.sum() + 1e-10)

        return float(jensenshannon(ref_hist, test_hist))
