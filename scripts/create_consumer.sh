HOST="${HOST:-localhost:5000}"

curl \
	-X POST \
	--header 'Content-Type: application/json' \
	--data-binary @- \
"http://${HOST}/consumers" <<EOF
{
	"name": "$1",
	"active": true,
	"credit": 0,
	"karma": 0
}
EOF
