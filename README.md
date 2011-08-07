ldapper
=======

ldap server for Man-Up. 

Takes a University of Manchester student id in an HTTP POST request and returns
json containing information retireved about them from the university's ldap
server.

If you are on a computer in the UoM school network:
    ./run_cs_server.sh

If you are not on a computer in the school network:
    ./run_test_server.sh <YOUR_CS_USERNAME>
(With no arguments it will use the cs name in the script)

To test the server:
    curl localhost:8080/lookup?uman_id=7145461
Should bring up some idiots information.

More generally:
    curl localhost:8080/lookup?uman_id=<A_UoM_STUDENT_ID>
Will return information about that user.

HTTP GET has been tested, but POST should work too.

* The returned data is in json. 
* If no data is retrieved it will return null.
* If it cannot connect to the LDAP server it will return a 500 error
