import sys
import logging
import codecs

sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)
sys.stdin = codecs.getreader('utf8')(sys.stdin)

logging.basicConfig( \
	stream=sys.stderr, \
	level=logging.WARN, \
	format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s.%(funcName)s %(message)s', \
	datefmt="%Y-%m-%dT%H:%M:%S" \
)
