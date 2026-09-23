"""Strategy probe, re-exported from the installed package.

The implementation lives in ``quant_core.testing.probe`` so that a downstream
package can use it without copying anything. This module stays at this path for
anything that imported it from here.
"""

from quant_core.testing.probe import CASH, Observation, ProbeResult, probe

__all__ = ["CASH", "Observation", "ProbeResult", "probe"]
