HOST="${HOST:-localhost:5000}"

curl \
	-X POST \
	--header 'Content-Type: application/json' \
	--data-binary @- \
"http://${HOST}/products" <<EOF
{
	"name": "$1",
	"price": $2,
	"active": true,
	"on_stock": true

}
EOF
