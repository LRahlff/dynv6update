# dynv6update
here is a script for updating the nameserver on dynv6.com

Add your zone and sub in the conf.json file. Delete the 'A' or 'AAAA', if you dont want to update both.

Also add for every entry (block in the conf file) one HTTP-Key of the zone in the my.cred file.
You can also delete the second block, if you only want to update one domain.

In the code there is a request to the os for getting the IP6 an a request to the fritzbox for getting the ipv4. Maybe you have to update these for your purpose. The script has already an request to a website for getting the ip. Maybe you can just exclude the request to the fritzbox and os.

There are some maybe helpful files for getting a systemd job running every hour, for starting the script.