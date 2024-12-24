import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")

# If you want to be more specific, you can suppress certain types of warnings like this:
# Suppress warnings related to model weights not being used (specific to the table transformer model)
warnings.filterwarnings("ignore", message=".*weights of the model checkpoint.*")

# Suppress warnings related to deprecated 'max_size' parameter
warnings.filterwarnings("ignore", message=".*The `max_size` parameter is deprecated.*")