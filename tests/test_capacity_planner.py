"""Capacity planner (research/workarounds-maestro-resources-2026-10-05.md): a pure function over fake readings. No device, simulator or Maestro."""
import itertools, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

R = sf.Reading
VM_STAT = """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                     3845.
Pages active:                                 416740.
Pages inactive:                               412115.
Pages speculative:                              3316.
Pages throttled:                                   0.
"""
BOOTED = """== Devices ==
-- iOS 26.4 --
    shotfleet-iphone-17-pro-max-1 (6FA6F47A-7974-4B5C-BCC6-B6E903F0445D) (Booted)
    shotfleet-iphone-17-pro-max-2 (44D31904-1D8C-4FC4-BE1A-7B5CC77AF8A5) (Booted)
    paid-review-iphone (11111111-2222-3333-4444-555555555555) (Booted)
"""


class Plan(unittest.TestCase):
    def test_a_quiet_mac_gets_what_it_asked_for(self):  # 2026-10-05: 404 s, 0 problems, 4 simulators
        p = sf.plan_capacity(4, "ios", R(avail_gb=20, total_gb=32, swap_used_gb=0.5, load1=3, cores=10, pressure="1"))
        self.assertEqual((p.n, p.level, p.notes), (4, "ok", ()))
        self.assertEqual(sf.capacity_message(p, 4, R()), "")

    def test_the_gate_start_state_runs_one_device(self):  # load 284, swap 17 GB of 18 GB: the 55 minute run
        p = sf.plan_capacity(4, "ios", R(avail_gb=8, swap_used_gb=17, load1=284, cores=10, pressure="2"))
        self.assertEqual((p.n, p.level), (1, "short")); self.assertTrue(any("swap" in n for n in p.notes))

    def test_swap_left_over_from_an_earlier_peak_does_not_matter_when_memory_is_free(self):  # gate end: swap 6 GB, free 73 %, ran fine
        self.assertEqual(sf.plan_capacity(4, "ios", R(avail_gb=20, swap_used_gb=6, cores=10, pressure="1")).n, 4)
        self.assertEqual(sf.plan_capacity(4, "ios", R(avail_gb=20, swap_used_gb=12, cores=10, pressure="1")).n, 4)  # the swap rule needs short memory too

    def test_memory_sets_the_number_of_simulators(self):
        p = sf.plan_capacity(4, "ios", R(avail_gb=7.5, cores=10, pressure="1"))  # (7.5 - 1.5 - 2) // 2 = 2
        self.assertEqual((p.n, p.level), (2, "tight"))
        self.assertEqual(sf.plan_capacity(4, "ios", R(avail_gb=4, cores=10)).n, 1)

    def test_simulators_of_the_pool_that_are_booted_cost_no_more_memory(self):  # 2026-10-05 15:00: 4 pool simulators up, 6.9 GB available, level 2
        p = sf.plan_capacity(4, "ios", R(avail_gb=6.9, swap_used_gb=6.4, load1=828, cores=10, pressure="2", booted_ours=4))
        self.assertEqual(p.n, 2)  # by memory all 4 fit; elevated pressure halves
        self.assertEqual(sf.plan_capacity(4, "ios", R(avail_gb=6.9, cores=10, pressure="1", booted_ours=4)).n, 4)

    def test_elevated_pressure_halves_like_fit_parallel(self):
        self.assertEqual(sf.plan_capacity(4, "ios", R(avail_gb=30, cores=10, pressure="2")).n, 2)
        self.assertEqual(sf.plan_capacity(1, "ios", R(avail_gb=30, cores=10, pressure="2")).n, 1)
        self.assertEqual(sf.plan_capacity(3, "ios", R(avail_gb=30, cores=10, pressure="2")).n, 1)

    def test_critical_pressure_is_reported_not_raised(self):  # the caller keeps fit_parallel's refusal; exit codes stay as they are
        p = sf.plan_capacity(4, "ios", R(avail_gb=30, cores=10, pressure="4"))
        self.assertEqual((p.n, p.level), (1, "critical"))

    def test_cores_limit_android_to_two_cores_per_emulator(self):  # E1: a 2-core runner passed with 1, 4+ cores for 2
        self.assertEqual(sf.plan_capacity(2, "android", R(avail_gb=30, cores=2)).n, 1)
        self.assertEqual(sf.plan_capacity(2, "android", R(avail_gb=30, cores=4)).n, 2)
        self.assertEqual(sf.plan_capacity(4, "android", R(avail_gb=30, cores=10)).n, 4)

    def test_android_emulators_want_three_gb_each(self):
        self.assertEqual(sf.plan_capacity(4, "android", R(avail_gb=10.6, cores=10)).n, 2)  # (10.6 - 3.5) // 3
        self.assertEqual(sf.plan_capacity(4, "android", R(avail_gb=15, cores=10)).n, 3)

    def test_nothing_readable_means_no_change(self):
        self.assertEqual(sf.plan_capacity(4, "ios", R()), sf.Plan(4, "ok", ()))

    def test_the_answer_is_always_between_one_and_want(self):
        for want, plat, avail, swap, press, cores, ours in itertools.product(
                (1, 2, 4, 8), ("ios", "android"), (None, 0, 3, 9, 40), (None, 0, 12, 25), ("", "1", "2", "4"), (None, 1, 2, 10), (0, 2, 4)):
            p = sf.plan_capacity(want, plat, R(avail_gb=avail, swap_used_gb=swap, pressure=press, cores=cores, booted_ours=ours))
            self.assertTrue(1 <= p.n <= want, (want, plat, avail, swap, press, cores, p))
            if p.n < want: self.assertTrue(p.notes, "a reduction always says why")


class Message(unittest.TestCase):
    def test_it_names_the_numbers_it_saw_and_what_to_close(self):
        r = R(avail_gb=4.2, swap_used_gb=17.0, load1=284, cores=10, pressure="2", booted_other=3)
        m = sf.capacity_message(sf.plan_capacity(4, "ios", r), 4, r)
        for part in ("short of memory", "1 device at once instead of 4", "4.2 GB memory available", "17.0 GB swap", "load 284 on 10 cores",
                     "3 other simulators/emulators booted", "Close Xcode, Android Studio", "./gradlew --stop", "lower `parallel`"):
            self.assertIn(part, m)

    def test_a_busy_mac_with_no_reduction_gets_a_gentler_head(self):
        r = R(avail_gb=30, cores=10, pressure="1", swap_used_gb=0, load1=5)
        self.assertEqual(sf.capacity_message(sf.Plan(4, "tight", ("x",)), 4, r)[:17], "this Mac is busy ")


class Readers(unittest.TestCase):
    def test_vm_stat(self):  # (3845 + 412115 + 3316) pages of 16 KiB
        self.assertAlmostEqual(sf.parse_vm_stat(VM_STAT), 419276 * 16384 / 2**30, places=6)
        self.assertIsNone(sf.parse_vm_stat("")); self.assertIsNone(sf.parse_vm_stat("Pages free: 3.\n"))

    def test_swap_and_load(self):
        self.assertAlmostEqual(sf.parse_swap_used_gb("total = 7168.00M  used = 6383.19M  free = 784.81M  (encrypted)"), 6.2336, places=3)
        self.assertEqual(sf.parse_swap_used_gb("total = 18.00G  used = 17.00G  free = 1.00G"), 17.0)
        self.assertIsNone(sf.parse_swap_used_gb("garbage"))
        self.assertEqual(sf.parse_load1("{ 828.41 423.28 236.45 }"), 828.41); self.assertIsNone(sf.parse_load1(""))

    def test_booted_simulators_are_split_into_ours_and_others(self):
        self.assertEqual(sf.count_booted(BOOTED), (2, 1)); self.assertEqual(sf.count_booted("== Devices ==\n"), (0, 0))

    def test_the_reader_never_raises_and_returns_a_reading(self):  # reads this machine's vm_stat/sysctl only; no simulator is started
        self.assertIsInstance(sf.read_capacity("android"), sf.Reading)


if __name__ == "__main__":
    unittest.main()
