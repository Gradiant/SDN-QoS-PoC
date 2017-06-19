if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters"
    echo "usage send_video.sh VIDEO_FILE"
    exit 1
fi

vlc-wrapper -I "dummy" --loop $1 --sout "#duplicate{dst=rtp{dst=10.0.0.3,port=5004,mux=ts},dst=rtp{dst=10.0.0.4,port=5004,mux=ts}}"
