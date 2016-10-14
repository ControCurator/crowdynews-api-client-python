import logging
import json
from frigg.frigg import Frigg

logger = logging.getLogger(__name__)

if __name__ == "__main__":
	frigg = Frigg({
		"symbol":"BRADANFEASA_TEST",
		"clientId":"2d264db29afdd8876d2f6d76b6867855",
		"clientSecret":"9da7fb4961b346ec112eb97391f49548d1d3d9f9d251c510e86687c39a47628d",
		"authServerDomain": "https://auth-test.crowdynews.com",
		"authServerVersion": "v1"
	})
	print frigg.token()
