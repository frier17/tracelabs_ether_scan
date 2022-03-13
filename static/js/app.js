// Define javascript functions for pulling and parsing information
// Use the axios for HTTP calls
const BASE_URL = 'http://localhost:8000';

var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
  return new bootstrap.Popover(popoverTriggerEl)
});


// Display result upon getting data
// Render table upon getting data
function processTransactions(tranx) {
    /**
    * Retrieve only needed fields for demo purposes
    * Accepted fields will include:
     'Tranx Hash',
    'Block hash',
    'Block height',
    'Total',
    'Fess',
    'Gas Used',
    'Gas price',
    'confirmed',
    'received',
    'Age',
    'Sending Address',
    'Receiving Address',
    */
    let fields = ['hash', 'block_hash', 'block_height', 'total', 'fees', 'gas_used', 'gas_price', 'confirmed', 'received', 'age', 'inputs', 'outputs'];
    let tableData = [];

    tranx.forEach(entry => {
        let transaction = {};
        for(const [key, value] of Object.entries(entry)) {
            if(fields.includes(key)) {
                if(key == 'inputs' || key == 'outputs') {
                    let addr = value[0]['addresses'].pop();
                    transaction[key] = addr;
                } else {
                    transaction[key] = value;
                }
            }
        }
        tableData.push(Object.values(transaction));
    });
    return tableData;
}

function scan(event) {
    event.preventDefault();
    // Display loading bar
    $('#loading-bar').toggleClass('collapse');
    let address = event.target.elements['address'].value;
    let block = event.target.elements['block'].value;
    postData = {"address": `${address}`, "block": `${block}` };
    // post object using axios
    axios.post(
    BASE_URL + '/scan', postData,
    {headers: {"Content-Type": "application/json", "Accept": "application/json"}}).then(response => {
        data = response.data;
        let addressData = data['address_monetary_summary'];
        let totalSent = Number(addressData['total_sent']) / Math.pow(10, 18);
        let totalReceived = Number(addressData['total_received']) / Math.pow(10, 18);
        // parse data to HTML structure
        $('[data-summary-field="address"]').text(addressData['address']);
        $('[data-summary-field="total-received"]').text(Number(addressData['total_received']) / Math.pow(10, 18));
        $('[data-summary-field="total-sent"]').text(Number(addressData['total_received']) / Math.pow(10, 18));
        $('[data-summary-field="balance"]').text(Number(addressData['balance']) / Math.pow(10, 18));
        $('[data-summary-field="unconfirmed-balance"]').text(Number(addressData['unconfirmed_balance']) / Math.pow(10, 18));
        $('[data-summary-field="final-balance"]').text(Number(addressData['final_balance']) / Math.pow(10, 18));
        $('[data-summary-field="final-n-tx"]').text(addressData['final_n_tx']);
        $('[data-summary-field="fiat-currency"]').text(addressData['fiat_currency']);
        $('[data-summary-field="total-money-sent"]').text(addressData['total_money_sent']);
        $('[data-summary-field="money-balance"]').text(addressData['money_balance']);

        let transactions = processTransactions(data['transaction_lists']);

        // Plot graph using High Chart plugin
        Highcharts.chart('graph', {
            chart: { type: 'column'},
            title: {text: 'Comparison of sent and received token amounts'},
            xAxis: { categories: ['Sent Token', 'Received Token'], crosshair: true},
            yAxis: {
            min: 0,
            title: {text: 'Quantity'}
            },
            series: [
            {
                name: 'Sent Token',
                data: [totalSent]
            },
            {
                name: 'Received Token',
                data: [totalReceived]
            },

            ]
        });
        // DataTable

        $('#grid').DataTable({
            data: transactions,
            columns: [
                {title: "block hash"},
                {title: "block height"},
                {title: "Hash"},
                {title: "total"},
                {title: "fees"},
                {title: "gas used"},
                {title: "gas price"},
                {title: "confirmed"},
                {title: "received"},
                {title: "inputs"},
                {title: "outputs"},
                {title: "age"},
            ],
            scrollX: true
        });
        setTimeout(() => {
            $('#loading-bar').toggleClass('collapse');
            $('#result').removeClass('collapse');
        }, 5000);


    }).catch(error => {
        console.log(error);
    })

}