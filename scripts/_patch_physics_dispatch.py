"""One-shot patch: route physics.py over-clutching through category_profiles.

Applies three surgical replacements to motoquant/physics.py:
  1. _precompute(): add self._profile setup
  2. Over-clutching tier: replace peak_hp gate with profile.over_clutch_factor
  3. Launch RPM floor clamp: replace peak_hp gate with profile.launch_floor_factor
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHYS = ROOT / "motoquant" / "physics.py"

with open(PHYS, "rb") as f:
    src = f.read()

# 1. Add profile lookup at end of _precompute
old1 = b"        self._env_model = EnvironmentalModel(c)\r\n        self.rho = self._env_model.rho\r\n        self.cd_a = c.aero.cd_a_effective  # static reference Cd*A\r\n        self.v_wind = self._env_model.v_headwind\r\n        self.power_correction = self._env_model.power_correction\r\n"

new1 = (
    b"        self._env_model = EnvironmentalModel(c)\r\n"
    b"        self.rho = self._env_model.rho\r\n"
    b"        self.cd_a = c.aero.cd_a_effective  # static reference Cd*A\r\n"
    b"        self.v_wind = self._env_model.v_headwind\r\n"
    b"        self.power_correction = self._env_model.power_correction\r\n"
    b"\r\n"
    b"        # Category-flavoured physics dispatch (April 30, 2026).\r\n"
    b"        # Look up per-cluster profile. If category_tag is unset, auto-\r\n"
    b"        # derive one from engine spec so legacy saved configs still get\r\n"
    b"        # category-aware behaviour (keeps the over-clutching tier alive\r\n"
    b"        # for old DB rows that pre-date the category_tag field).\r\n"
    b"        from .category_profiles import derive_category_tag, get_profile\r\n"
    b"        tag = c.category_tag\r\n"
    b"        if not tag:\r\n"
    b"            tag = derive_category_tag(\r\n"
    b'                manufacturer="", model_name="",\r\n'
    b"                displacement_cc=c.engine.displacement_cc,\r\n"
    b"                peak_power_hp=c.engine.peak_power_hp,\r\n"
    b"                stroke_type=c.engine.stroke_type,\r\n"
    b"                category=None,\r\n"
    b"            )\r\n"
    b"        self._profile = get_profile(tag)\r\n"
)

assert src.count(old1) == 1, f"precompute marker count: {src.count(old1)}"
src = src.replace(old1, new1)


# 2. Replace the over-clutching tier
EM = "—".encode("utf-8")  # em-dash
old2 = (
    b"                    peak_hp = cfg.engine.peak_power_hp or 0.0\r\n"
    b"                    if peak_hp < 60.0 and slip_speed > 0:\r\n"
    b"                        # Rate-limit engine deceleration to a realistic launch\r\n"
    b"                        # value. Tier the cap by power: very-low-power bikes\r\n"
    b"                        # get more aggressive launches (riders rev higher and\r\n"
    b"                        # bog harder).\r\n"
    b"                        if peak_hp < 22.0:\r\n"
    b"                            max_decel_rad_per_s2 = 350.0   # ~3300 rpm/s " + EM + b" hard launch\r\n"
    b"                            over_clutch_factor = 0.50\r\n"
    b"                        elif peak_hp < 30.0:\r\n"
    b"                            max_decel_rad_per_s2 = 280.0   # ~2700 rpm/s\r\n"
    b"                            over_clutch_factor = 0.40\r\n"
    b"                        else:\r\n"
    b"                            max_decel_rad_per_s2 = 200.0   # ~1900 rpm/s\r\n"
    b"                            over_clutch_factor = 0.30\r\n"
    b"                        max_back_torque = max_decel_rad_per_s2 * max(I_e_local, 0.001)\r\n"
    b"                        headroom = max(0.0, T_clutch_max - abs(T_e_crank))\r\n"
    b"                        over_clutch_extra = min(headroom * over_clutch_factor, max_back_torque)\r\n"
    b"                        T_transmitted = min(abs(T_e_crank) + over_clutch_extra, T_clutch_max)\r\n"
    b"                    else:\r\n"
    b"                        T_transmitted = min(abs(T_e_crank), T_clutch_max)\r\n"
)

new2 = (
    b"                    peak_hp = cfg.engine.peak_power_hp or 0.0\r\n"
    b"                    # Category-flavoured over-clutching dispatch.\r\n"
    b"                    # Reads tier knobs from self._profile (set in _precompute).\r\n"
    b"                    # Profile.over_clutch_factor==0 reproduces the pre-April-30\r\n"
    b"                    # legacy min(T_e_crank, T_clutch_max) behaviour for the\r\n"
    b"                    # litre-sport / cruiser clusters that don't need slip-launch.\r\n"
    b"                    prof = self._profile\r\n"
    b"                    if prof.over_clutch_factor > 0.0 and slip_speed > 0:\r\n"
    b"                        max_back_torque = prof.max_engine_decel_rads2 * max(I_e_local, 0.001)\r\n"
    b"                        headroom = max(0.0, T_clutch_max - abs(T_e_crank))\r\n"
    b"                        over_clutch_extra = min(headroom * prof.over_clutch_factor, max_back_torque)\r\n"
    b"                        T_transmitted = min(abs(T_e_crank) + over_clutch_extra, T_clutch_max)\r\n"
    b"                    else:\r\n"
    b"                        T_transmitted = min(abs(T_e_crank), T_clutch_max)\r\n"
)

assert src.count(old2) == 1, f"over-clutch marker count: {src.count(old2)}"
src = src.replace(old2, new2)


# 3. Replace the launch floor clamp gate
old3 = (
    b"                    if peak_hp < 60.0:\r\n"
    b"                        # 2-strokes: clamp at tuned_rpm (where the expansion\r\n"
    b"                        # chamber peaks) " + EM + b" peak_torque_rpm is BELOW the actual\r\n"
    b"                        # peak for piston-port 2T. 4T: peak_torque_rpm is the\r\n"
    b"                        # actual torque peak so use that directly.\r\n"
    b"                        if cfg.engine.stroke_type == 2 and cfg.engine.tuned_rpm:\r\n"
    b"                            floor_rpm = cfg.engine.tuned_rpm\r\n"
    b"                        else:\r\n"
    b"                            floor_rpm = cfg.engine.peak_torque_rpm\r\n"
    b"                        floor_omega = floor_rpm * RPM_TO_RADS\r\n"
    b"                        if omega_e < floor_omega:\r\n"
    b"                            omega_e = floor_omega\r\n"
)

new3 = (
    b"                    if prof.launch_floor_factor > 0.0:\r\n"
    b"                        # Cluster-aware launch RPM floor. 2-strokes pin at\r\n"
    b"                        # tuned_rpm (expansion-chamber resonance, above\r\n"
    b"                        # peak_torque_rpm); 4T pins at peak_torque_rpm.\r\n"
    b"                        if cfg.engine.stroke_type == 2 and cfg.engine.tuned_rpm:\r\n"
    b"                            floor_rpm = cfg.engine.tuned_rpm * prof.launch_floor_factor\r\n"
    b"                        else:\r\n"
    b"                            floor_rpm = cfg.engine.peak_torque_rpm * prof.launch_floor_factor\r\n"
    b"                        floor_omega = floor_rpm * RPM_TO_RADS\r\n"
    b"                        if omega_e < floor_omega:\r\n"
    b"                            omega_e = floor_omega\r\n"
)

assert src.count(old3) == 1, f"floor-clamp marker count: {src.count(old3)}"
src = src.replace(old3, new3)


with open(PHYS, "wb") as f:
    f.write(src)
print(f"physics.py patched ({len(src)} bytes)")
