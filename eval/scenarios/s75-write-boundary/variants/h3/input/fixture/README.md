# Appointment scheduler

The support team needs a function that finds the earliest shared appointment slot. Start with the board and T-52 brief. Scheduling rules are in contract.md; the supplied office hours are in evidence/route-observations.md. Run the focused check here:

    python3 -B tests/test_deploy_review.py

The test entry is a protected check. Implement the scheduler in src/deploy_review.py.