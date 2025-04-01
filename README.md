Download source from this link: https://drive.google.com/drive/folders/1iGpvn_Q6C556q8lnMhKjt3ZmnhKJ3Wvp
# How to load jitsi docker source
docker load -i jitsi-jicofo.tar

docker load -i jitsi-jigasi.tar

docker load -i jitsi-jvb.tar

docker load -i jitsi-web.tar

unzip stabel-10133-1

Plz go to extracted directory

cp env.example .env

./gen-passwords.sh

mkdir -p ~/.jitsi-meet-cfg/{web,transcripts,prosody/config,prosody/prosody-plugins-custom,jicofo,jvb,jigasi,jibri}

add this environment variables into .env file

`PUBLIC_URL=[ipv4]:${HTTPS_PORT} e.g. 192.168.148.152:${HTTPS_PORT}`

`LOCAL_ADDRESS=[ipv4] e.g. 192.168.148.152`

`JVB_ADVERTISE_IPS=[ipv4] e.g. 192.168.148.152`

docker compose up -d
