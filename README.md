# WCanon
Python WiFi Encrypted Chat CLI Application to communicate with peers in the network; encrypted with 2048 bit RSA

## Basic Description
This application provides a interface to communicate with users under the same network.

It runs on two threads. The main thread and a server thread. The server thread starts immediately when the app starts and starts to listent to the defined port. If any connection is made the messages received are displayed along with the IP address.

The application also provides a RSA 2048 bit encrypted communication amongs the users. This means the messages will be communicated at max length of 256 bytes. To achive this, the application needs the PyCrypto library which can be added to your python library using:<br/>
\>\>  `pip install pycrypto`

The main thread provides a CLI for users of the following functionalities
<ul>
  <li> List all users in a wifi network that's using the application</li>
  <li> Connect to a user</li>
  <li> Send messages to the connected user</li>
  <li> Shutdown the app</li>
</ul>

### Important!
If app crashes, use `lsof -i tcp:4818` to get the PID (process ID) and then use
`kill -9 <PID>` to kill the process.

## List of commands
<ul>
  <li> list -> Lists all users avaliable under the network</li>
  <li> connect 0.0.0.0 -> Connect to the ip address</li>
  <li> exit -> Exit app</li>
</ul>
