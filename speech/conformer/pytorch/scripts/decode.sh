python3 main.py validate --checkpoints.save_checkpoint_path "./checkpoint" --trainer.num_epochs 240  --ipu_options.device_iterations 10
python3 main.py recognize --train_dataset.dtype 'FLOAT32' --val_dataset.dtype 'FLOAT32' --trainer.dtype 'FLOAT32' --ipu_options.enable_half_partials False
