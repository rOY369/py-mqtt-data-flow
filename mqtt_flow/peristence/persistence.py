import persistqueue
from retry import retry
import threading
import time
import json
from mqtt_flow.utils.helpers import get_logger

logger = get_logger("persistence")


class UploadError(Exception):
    pass


class MockPersistence:

    def append_to_batch(self, data_point):
        pass

    def put_batch(self, batch):
        pass

    def start(self, uploader):
        pass


class Persistence:
    DEFAULT_UPLOAD_INTERVAL = 5
    DEFAULT_INIT_RETRY_CONFIG = {
        "tries": 3,
        "delay": 1,
        "max_delay": 8,
        "backoff": 2,
    }

    DEFAULT_BATCH_RETRY_CONFIG = {
        "tries": -1,
        "delay": 1,
        "max_delay": 8,
        "backoff": 2,
    }
    DEFAULT_BATCH_SIZE = 10
    DEFAULT_BATCH_UPLOAD_MIN_DELAY = 60

    def __init__(self, config):
        self.name = config.get("name")
        self.main_path = config.get("main_path")
        self.backup_path = config.get("backup_path")
        self.batch_size = config.get("batch_size", self.DEFAULT_BATCH_SIZE)
        self.batch_upload_min_delay = config.get(
            "batch_upload_min_delay",
            self.DEFAULT_BATCH_UPLOAD_MIN_DELAY,
        )
        self.upload_interval = config.get(
            "upload_interval", self.DEFAULT_UPLOAD_INTERVAL
        )
        self.batch = []
        self._batch_lock = threading.Lock()

        try:
            self._pqueue = self._create_persistence_queue(self.main_path)
        except:
            if self.backup_path:
                self._pqueue = self._create_persistence_queue(self.backup_path)

    @retry(exceptions=(Exception,), **DEFAULT_INIT_RETRY_CONFIG)
    def _create_persistence_queue(self, path):
        return persistqueue.FIFOSQLiteQueue(
            path=path,
            auto_commit=False,
            multithreading=True,
        )

    def put_batch(self):
        """
        Puts the given batch into the given persist queue to be uploaded later.

        Args:
            batch(list): list of data points.
        """
        batch = self.batch.copy()

        if isinstance(batch, list) or isinstance(batch, dict):
            batch = json.dumps(batch)

        self._pqueue.put_nowait(batch)

        self.batch = []

    def append_to_batch(self, data_point):
        with self._batch_lock:
            self.batch.append(data_point)

            if len(self.batch) >= self.batch_size:
                self.put_batch()

    def put_batch_regular_intervals(self):
        while True:
            time.sleep(self.batch_upload_min_delay)
            if self.batch:
                with self._batch_lock:
                    self.put_batch()

    @retry(
        exceptions=(UploadError,),
        **DEFAULT_BATCH_RETRY_CONFIG,
    )
    def upload_batch(self, uploader):
        """
        Gets batch from the persist queue of the given queue type and uploads
        it via the given uploader.
        Args:
            uploader(): instance of uploader.
        """
        try:
            batch = self._pqueue.get_nowait()
        except persistqueue.exceptions.Empty:
            logger.info(f"persist_queue_empty for {self.name}")
        else:
            logger.info(f"persist_queue_upload_try for {self.name}")

            try:
                batch_to_upload = json.loads(batch)
            except json.decoder.JSONDecodeError:
                batch_to_upload = batch

            try:
                upload_response = uploader.upload_persisted_batch(
                    batch_to_upload
                )
            except Exception:
                logger.exception(f"persist_queue_upload_fail for {self.name}")
                upload_response = False

            if not upload_response:
                logger.info(f"persist_queue_upload_fail for {self.name}")
                raise UploadError()
            else:
                logger.info(f"persist_queue_upload_success for {self.name}")

            self._pqueue.task_done()

    def start(self, uploader):
        threading.Thread(target=self.start_upload, args=(uploader,)).start()
        threading.Thread(target=self.put_batch_regular_intervals).start()

    def start_upload(self, uploader):
        while True:

            if uploader.is_connected():
                self.upload_batch(uploader)
            time.sleep(self.upload_interval)
