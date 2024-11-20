


const webSocket = () => {
    let url = `ws://${window.location.host}/ws/`;
    console.log("Socket path: ", url);
    const socket = new WebSocket(url);
    socket.onmessage = function (event) {
        let data = JSON.parse(event.data);
        console.log("Received Data: ", data);
        try {
            let testWebSocket = document.querySelector('#testWebSocket');
            if (testWebSocket) {
                testWebSocket.innerHTML = JSON.stringify(data);
            };
        } catch (error) {
            console.log("Test web socket data failed: ", error);
        };
    };
};