Feature: Scan ethereum blockchain
  """
  As a user
  I want to scan wallet or ethereum addresses
  So I can view lists of transactions associated with a given address,
  view statistics of the transactions, example the maximum amount of ether transferred
  view the historical monetary value transacted on the address/wallet
  Transaction statistics can cover the following:
  + Max and Min amount of ether transacted
  + Total number of transactions made per day
  + Total number of transactions associated with the address
  + Current monetary value of wallet balance
  """

  Scenario: Retrieve transaction list for a wallet
    Given a user wishes to view list of transaction
    When the user posts wallet address and other parameters
    Then the application validates the wallet address
    And the application performs API call to etherscan.io for transaction lists
    And the application parses the return data to produce an information object
    And the application appends the defined statistics for the transactions to the information object
    And the application returns the information object as json to the caller for further processing