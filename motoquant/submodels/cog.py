"""
System centre of mass — bike + rider (2026-10 physics epoch, round 2)
=====================================================================
The wheelie limit (``WheelieModel``) and the longitudinal load transfer
(``WeightTransferModel``) both act at the centre of mass of the WHOLE system
that accelerates: the motorcycle with its fluids AND the rider. Before round 2
both read ``ChassisParams.cog_height_mm`` directly. That field holds a
bike-sized value (540 mm on the K5, 530-620 mm across the catalog importer),
but no combined bike + rider CoG is that low — a 75 kg rider sits ~0.95-1.0 m
above the ground on a sport bike — so the wheelie ceiling came out at
~1.35-1.5 g and never bound below the tyre limit. Real 200 hp litre bikes are
wheelie-limited off the line (~1.0-1.1 g) and power-limited above ~2nd gear.

Composition (documented assumptions):

* ``chassis.cog_height_mm`` is the bike's own CoG height — dry mass plus
  fluids, no rider (the reading every catalog value is consistent with).
* ``chassis.front_weight_pct`` is the static front-wheel load share. The
  rider's seated CoG is taken to lie at the same longitudinal position as the
  bike's: a crouched rider's CoG sits within a few centimetres of a sport
  bike's system CoG fore-aft, so ``front_weight_pct`` holds for any rider
  mass and changing the rider mass moves the CoG only vertically.
* The rider's CoG height is ``seat_height - static_sag + k * stature``
  (``constants.RIDER_COG_ABOVE_SEAT_PER_STATURE``, an anthropometric
  derivation documented there): seat height from the spec, the laden rear sag
  from ``suspension.static_sag_mm``, stature from ``rider.height_cm``.
* The rider's body movement (``RiderParams.cog_offset(t)``: forward lean at
  launch, slightly rearward in the tuck) moves the RIDER's mass; the system
  CoG moves by ``m_rider / m_total`` of it.
* A swingarm extension moves the rear axle back: the front-axle-to-CoG
  distance is unchanged, the rear-axle-to-CoG distance grows by the full
  extension (previously only ``front_weight_pct`` of it).

Masses use the configured (start-of-run) values; fuel burn over a pass is
< 0.1 kg.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import RIDER_COG_ABOVE_SEAT_PER_STATURE
from ..models import BikeConfig


@dataclass(frozen=True)
class SystemCoG:
    """Combined bike + rider centre of mass (static, rider in the seat)."""

    #: Wheelbase including any swingarm extension (m).
    wheelbase_m: float
    #: Combined CoG height above the ground (m).
    height_m: float
    #: Front axle -> combined CoG, horizontal (m).
    l_f_m: float
    #: m_rider / m_total — the share of a rider-body shift the system CoG sees.
    rider_shift_frac: float
    #: Rider CoG height above the ground (m) — diagnostics.
    rider_height_m: float
    #: Bike (dry + fluids) CoG height (m) — diagnostics.
    bike_height_m: float


def rider_cog_height_m(cfg: BikeConfig) -> float:
    """Rider's seated CoG height above the ground (m)."""
    c = cfg.chassis
    seat_laden_m = (c.seat_height_mm - cfg.suspension.static_sag_mm) / 1000.0
    return seat_laden_m + RIDER_COG_ABOVE_SEAT_PER_STATURE * (
        cfg.rider.height_cm / 100.0
    )


def system_cog(cfg: BikeConfig) -> SystemCoG:
    """Compose the bike + rider centre of mass from the config."""
    c = cfg.chassis
    m_bike = c.dry_mass_kg + c.fluid_mass_kg
    m_rider = c.rider_mass_kg
    m_total = m_bike + m_rider
    h_bike = c.cog_height_mm / 1000.0
    h_rider = rider_cog_height_m(cfg)
    if m_total <= 0.0:
        raise ValueError(f"total mass must be > 0 (got {m_total!r} kg)")
    if not (h_bike > 0.0) or not (h_rider > 0.0):
        raise ValueError(
            f"CoG heights must be > 0 (bike {h_bike!r} m, rider {h_rider!r} m)"
        )
    height = (m_bike * h_bike + m_rider * h_rider) / m_total
    wheelbase_stock = c.wheelbase_mm / 1000.0
    wheelbase = c.wheelbase_m
    # Front axle -> CoG is fixed by the bike; a swingarm extension only moves
    # the rear axle back.
    l_f = wheelbase_stock * (1.0 - c.front_weight_pct)
    return SystemCoG(
        wheelbase_m=wheelbase,
        height_m=height,
        l_f_m=l_f,
        rider_shift_frac=m_rider / m_total,
        rider_height_m=h_rider,
        bike_height_m=h_bike,
    )
