import json
import numpy as np
try:
    json.dumps({'pcr': np.float64(1.19)})
    print("np.float64 is serializable")
except Exception as e:
    print("np.float64 error:", type(e), e)
