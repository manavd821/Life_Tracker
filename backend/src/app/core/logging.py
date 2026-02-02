
import logging
import logging.config
from app.core.log_context import request_id_ctx
class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        record.request_id = request_id_ctx.get(None)
        return True
    
def setup_logging(log_level : str) -> None:
    logging_config = {
        "version" : 1,
        "disable_existing_loggers" : False,
        "formatters" : {
            "default" : {
                "format" : (
                    "%(asctime)s | %(levelname)s | %(name)s | req_id=%(request_id)s | %(message)s"
                )
            }
        },
        "filters" : {
            "request_id" : {
                "()" : "app.core.logging.RequestIdFilter"
            }
        },
        "handlers" : {
            "console": {
                "class" : "logging.StreamHandler",
                "formatter": "default",
                "filters" : ["request_id"],
                "stream"  : "ext://sys.stdout",
            }
        },
        "root" : {
            "level" : log_level,
            "handlers" : ["console"],
        },
        
    }
    
    logging.config.dictConfig(logging_config)