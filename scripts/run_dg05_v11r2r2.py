"""The V11R2R2 release-bound entrypoint.

The hardened runner implementation remains shared; this explicit successor
entrypoint is bound in the V11R2R2 execution census and never accepts the
consumed V11R2R1 manifest schema.
"""
from run_dg05_v11r2r1 import main


if __name__ == "__main__":
    main()
