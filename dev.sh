#!/bin/sh

FLASK_DEBUG=1 \
	FLASK_APP=webapi.py \
	flask run --host=0.0.0.0
