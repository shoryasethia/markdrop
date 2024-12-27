import warnings
import logging
import transformers

# Suppress specific warnings using the warnings module
warnings.filterwarnings("ignore", message=".*weights of the model checkpoint.*")
warnings.filterwarnings("ignore", message=".*The `max_size` parameter is deprecated.*")

# Set transformers logging level to ERROR
transformers.logging.set_verbosity_error()

# Suppress other libraries if necessary
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# Optional: Add a null handler to redirect all logs
logging.getLogger("transformers").addHandler(logging.NullHandler())
