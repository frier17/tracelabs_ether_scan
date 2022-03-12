// Define javascript functions for pulling and parsing information
// Use the axios for HTTP calls
const BASE_URL = 'http://localhost:8000';

function scan(data) {
    axios.post(BASE_URL + '/scan').then(response => {
        // process response into html
    }).catch(error => {
        console.log(error);
    });
}