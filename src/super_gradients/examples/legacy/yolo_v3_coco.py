# YoLo V3 (Big) Detection training on CoCo Dataset:
# mAP@0.5 ~ 56.8

# The code is optimized for running with a Mini-Batch of 64 examples... So depending on the amount of GPUs,
# you should change the "batch_accumulate" param in the training_params dict to be batch_size * gpu_num * batch_accumulate = 64.

# IMPORTANT: The final step estimates the IOU threshold differently, in order to boost the mAP score - so please run it
#            all the way to the final epoch

from super_gradients.training import SgModel, MultiGPUMode
from super_gradients.training.datasets import CoCoDetectionDatasetInterface
from super_gradients.training.utils.detection_utils import base_detection_collate_fn
from super_gradients.training.datasets.datasets_utils import ComposedCollateFunction, MultiScaleCollateFunction
from super_gradients.training.utils.detection_utils import YoloV3NonMaxSuppression
from super_gradients.training.metrics.detection_metrics import DetectionMetrics

collate_fn_holder = ComposedCollateFunction([base_detection_collate_fn, MultiScaleCollateFunction(320)])
yolo_v3_dataset_params = {"batch_size": 16,
                          "test_batch_size": 16,
                          "dataset_dir": "/data/coco/",
                          "s3_link": None,
                          "image_size": 320,
                          "test_collate_fn": base_detection_collate_fn,
                          "train_collate_fn": collate_fn_holder,
                          }

yolo_v3_arch_params = {"image_size": 320, "iou_t": 0.225, "multi_gpu_mode": "distributed_data_parallel"}

post_prediction_callback = YoloV3NonMaxSuppression()
model = SgModel('yolo_v3_spp_example', model_checkpoints_location='local', multi_gpu=MultiGPUMode.OFF,
                post_prediction_callback=post_prediction_callback)

coco_datasaet_interface = CoCoDetectionDatasetInterface(dataset_params=yolo_v3_dataset_params)
model.connect_dataset_interface(coco_datasaet_interface, data_loader_num_workers=8)
model.build_model('yolo_v3', arch_params=yolo_v3_arch_params, load_checkpoint=False)

yolo_v3_training_params = {"max_epochs": 273, 'lr_mode': "step", "lr_updates": [219, 246], "lr_decay_factor": 0.1,
                           "initial_lr": 0.00579, "batch_accumulate": 4,
                           "loss": "detection_loss", "criterion_params": {"model": model}, "optimizer": "SGD",
                           "optimizer_params": {"momentum": 0.937, "weight_decay": 0.000484, "nesterov": True},
                           "mixed_precision": True,
                           "train_metrics_list": [],

                           "valid_metrics_list": [DetectionMetrics(post_prediction_callback=post_prediction_callback,
                                                                   num_cls=len(
                                                                       coco_datasaet_interface.coco_classes))],
                           "loss_logging_items_names": ["GIoU", "obj", "cls", "Loss"],
                           "metric_to_watch": "mAP@0.50:0.95",
                           "greater_metric_to_watch_is_better": True}

model.train(training_params=yolo_v3_training_params)
