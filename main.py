"""Main orchestration module for the Ecologistic Intelligence ML pipeline."""

import argparse
import sys

from src.preprocessing.split_feature import run_full_preprocessing
from src.services.prediction_service import PredictionService
from src.training.train import run_full_training
from src.utils.logger import get_logger, setup_logger

logger = get_logger(__name__)


def run_preprocessing_only() -> bool:
    """Run only the preprocessing pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info("RUNNING PREPROCESSING PIPELINE")
    logger.info("=" * 70)

    try:
        run_full_preprocessing()
        logger.info("Preprocessing completed successfully")
        return True
    except Exception as exc:
        logger.error(f"Preprocessing failed: {exc}")
        return False


def run_training_only() -> bool:
    """Run only the training pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info("RUNNING TRAINING PIPELINE")
    logger.info("=" * 70)

    try:
        run_full_training()
        logger.info("Training completed successfully")
        return True
    except Exception as exc:
        logger.error(f"Training failed: {exc}")
        return False


def run_full_pipeline() -> bool:
    """Run complete pipeline: preprocessing -> training."""
    logger.info("\n" + "=" * 70)
    logger.info("STARTING FULL ML PIPELINE")
    logger.info("=" * 70)

    logger.info("\n[1/2] PREPROCESSING STAGE")
    logger.info("-" * 70)
    if not run_preprocessing_only():
        logger.error("Pipeline stopped: preprocessing failed")
        return False

    logger.info("\n[2/2] TRAINING STAGE")
    logger.info("-" * 70)
    if not run_training_only():
        logger.error("Pipeline stopped: training failed")
        return False

    logger.info("\n" + "=" * 70)
    logger.info("FULL PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 70)
    logger.info("Next steps:")
    logger.info("1. Use PredictionService for inference")
    logger.info("2. Use InterpretationService for explanation")
    logger.info("3. Start the FastAPI wrapper for frontend integration")
    logger.info("=" * 70 + "\n")
    return True


def demo_prediction() -> bool:
    """Run a sample prediction using saved artifacts."""
    logger.info("\n" + "=" * 70)
    logger.info("RUNNING PREDICTION DEMO")
    logger.info("=" * 70)

    try:
        service = PredictionService()
        result = service.predict(
            region="Western Europe",
            shipping_mode="Flight",
            category="Apparel",
            quantity=5,
            days_for_shipment=1,
            sales=100.0,
        ).to_dict()

        logger.info("PREDICTION RESULT")
        logger.info(f"Risk Level: {result['risk_level']}")
        logger.info(f"Risk Score: {result['risk_score']}%")
        logger.info(f"Probability: {result['risk_probability']:.3f}")
        logger.info(f"Explanation: {result['explanation']}")
        return True
    except Exception as exc:
        logger.error(f"Prediction demo failed: {exc}")
        return False


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ecologistic Intelligence ML Pipeline Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["full", "preprocess", "train", "predict"],
        default="full",
        help="Pipeline mode to run",
    )
    parser.add_argument("--log-file", type=str, default="pipeline.log", help="Log file name")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    setup_logger(__name__, log_file=args.log_file)

    logger.info(f"Starting Ecologistic Intelligence Pipeline (mode={args.mode})")

    if args.mode == "full":
        success = run_full_pipeline()
    elif args.mode == "preprocess":
        success = run_preprocessing_only()
    elif args.mode == "train":
        success = run_training_only()
    else:
        success = demo_prediction()

    if success:
        logger.info("Pipeline execution successful")
        return 0

    logger.error("Pipeline execution failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())

