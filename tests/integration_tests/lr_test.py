import shutil
import unittest
import os
from super_gradients import SgModel, ClassificationTestDatasetInterface
from super_gradients.training.metrics import Accuracy, Top5


class LRTest(unittest.TestCase):
    @classmethod
    def setUp(cls):
        # NAMES FOR THE EXPERIMENTS TO LATER DELETE
        cls.folder_name = 'lr_test'
        cls.training_params = {"max_epochs": 1,
                               "silent_mode": True,
                               "initial_lr": 0.1,
                               "loss": "cross_entropy", "train_metrics_list": [Accuracy(), Top5()],
                               "valid_metrics_list": [Accuracy(), Top5()],
                               "loss_logging_items_names": ["Loss"], "metric_to_watch": "Accuracy",
                               "greater_metric_to_watch_is_better": True}

    @classmethod
    def tearDownClass(cls) -> None:
        # ERASE THE FOLDER THAT WAS CREATED DURING THIS TEST
        if os.path.isdir(os.path.join('checkpoints', cls.folder_name)):
            shutil.rmtree(os.path.join('checkpoints', cls.folder_name))

    @staticmethod
    def get_trainer(name=''):
        model = SgModel(name, model_checkpoints_location='local')
        dataset_params = {"batch_size": 4}
        dataset = ClassificationTestDatasetInterface(dataset_params=dataset_params)
        model.connect_dataset_interface(dataset)
        model.build_model("resnet18_cifar", load_checkpoint=False)
        return model

    def test_function_lr(self):
        model = self.get_trainer(self.folder_name)

        def test_lr_function(initial_lr, epoch, iter, max_epoch, iters_per_epoch, **kwargs):
            return initial_lr * (1 - ((epoch * iters_per_epoch + iter) / (max_epoch * iters_per_epoch)))

        # test if we are able that lr_function supports functions with this structure
        training_params = {**self.training_params, "lr_mode": "function", "lr_schedule_function": test_lr_function}
        model.train(training_params=training_params)

        # test that we assert lr_function is callable
        training_params = {**self.training_params, "lr_mode": "function"}
        with self.assertRaises(AssertionError):
            model.train(training_params=training_params)

    def test_cosine_lr(self):
        model = self.get_trainer(self.folder_name)
        training_params = {**self.training_params, "lr_mode": "cosine", "cosine_final_lr_ratio": 0.01}
        model.train(training_params=training_params)

    def test_step_lr(self):
        model = self.get_trainer(self.folder_name)
        training_params = {**self.training_params, "lr_mode": "step", "lr_decay_factor": 0.1, "lr_updates": [4]}
        model.train(training_params=training_params)


if __name__ == '__main__':
    unittest.main()
