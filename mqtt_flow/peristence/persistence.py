import persistqueue
from retry import retry
import threading
import time
import json
from mqtt_flow.utils.helpers import get_logger


class UploadError(Exception):
    pass


class PersistenceQueueError(Exception):
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
        self.logger = get_logger("persistence")

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
        self._main_pqueue = None
        self._backup_pqueue = None

        try:
            self._main_pqueue = self._create_persistence_queue(self.main_path)
        except:
            self.logger.warning(
                f"Failed to create main persistence queue in {self.main_path}"
            )
            if self.backup_path:
                try:
                    self._backup_pqueue = self._create_persistence_queue(
                        self.backup_path
                    )
                except:
                    self.logger.warning(
                        f"Failed to create backup persistence queue in {self.backup_path}"
                    )

        if self._main_pqueue is None and self._backup_pqueue is None:
            raise PersistenceQueueError("Failed to create persistence queue")

    @retry(exceptions=(Exception,), **DEFAULT_INIT_RETRY_CONFIG)
    def _create_persistence_queue(self, path):
        return persistqueue.FIFOSQLiteQueue(
            path=path,
            auto_commit=False,
            multithreading=True,
        )

    def get_main_pqueue_size(self):
        if self._main_pqueue is None:
            return 0

        return self._main_pqueue.qsize()

    def get_backup_pqueue_size(self):
        if self._backup_pqueue is None:
            return 0

        return self._backup_pqueue.qsize()

    def put_batch(self):
        """
        Puts the given batch into the given persist queue to be uploaded later.

        Args:
            batch(list): list of data points.
        """
        batch = self.batch.copy()

        if isinstance(batch, list) or isinstance(batch, dict):
            batch = json.dumps(batch)

        try:
            self._main_pqueue.put_nowait(batch)
        except Exception:
            self.logger.warning(
                "Failed to put batch in main persist queue", exc_info=True
            )
            try:
                self._backup_pqueue.put_nowait(batch)
            except Exception:
                self.logger.warning(
                    "Failed to put batch in backup persist queue",
                    exc_info=True,
                )

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
    def upload_batch(self, pqueue, uploader):
        """
        Gets batch from the persist queue of the given queue type and uploads
        it via the given uploader.
        Args:
            uploader(): instance of uploader.
        """
        try:
            batch = pqueue.get_nowait()
        except persistqueue.exceptions.Empty:
            self.logger.debug(f"persist_queue_empty for {self.name}")
        else:
            self.logger.info(
                f"persist_queue_upload_try for {self.name}"
            )

            try:
                batch_to_upload = json.loads(batch)
            except json.decoder.JSONDecodeError:
                batch_to_upload = batch

            try:
                upload_response = uploader.upload_persisted_batch(
                    batch_to_upload
                )
            except Exception:
                self.logger.exception(
                    f"persist_queue_upload_fail for {self.name}"
                )
                upload_response = False

            if not upload_response:
                self.logger.info(f"persist_queue_upload_fail for {self.name}")
                raise UploadError()
            else:
                self.logger.info(
                    f"persist_queue_upload_success for {self.name}"
                )

            pqueue.task_done()

    def start(self, uploader):
        threading.Thread(target=self.start_upload, args=(uploader,)).start()
        threading.Thread(target=self.put_batch_regular_intervals).start()

    def start_upload(self, uploader):
        while True:

            if uploader.is_connected():
                if self._main_pqueue is not None:
                    self.upload_batch(self._main_pqueue, uploader)

                if self._backup_pqueue is not None:
                    self.upload_batch(self._backup_pqueue, uploader)

            time.sleep(self.upload_interval)
