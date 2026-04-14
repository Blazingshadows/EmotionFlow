import argparse
import torch

from training.affectnet import get_loaders, build_model, train_model, plot_training_history
from training.evaluation import evaluate


def main():
    parser = argparse.ArgumentParser(
        description="Train improved AffectNet MobileNetV2 and run evaluation"
    )
    parser.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip training and evaluate an existing checkpoint",
    )
    parser.add_argument(
        "--model",
        default="checkpoints_affectnet_yolo/mobilenetv2_best.pth",
        help="Model checkpoint path for evaluation",
    )
    args = parser.parse_args()

    if not args.skip_train:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")

        train_loader, val_loader, train_set = get_loaders()
        model = build_model().to(device)

        history = train_model(model, train_loader, val_loader, train_set, device)
        plot_training_history(history)

    evaluate(model_path=args.model)


if __name__ == "__main__":
    main()
