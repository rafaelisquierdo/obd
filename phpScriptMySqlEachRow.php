<?php
//Step1
 $db = mysql_connect("localhost","pi","raspberry"); 
 if (!$db) {
 die("Database connection failed miserably: " . mysql_error());
 }
//Step2
 $db_select = mysql_select_db("obd_database",$db);
 if (!$db_select) {
 die("Database selection also failed miserably: " . mysql_error());
 }
//Step3
$result = mysql_query("SELECT * FROM obdPi", $db);
 if (!$result) {
 die("Database query failed: " . mysql_error());
 }
//Step4
 $row = mysql_fetch_array($result); 
 /*echo "<h2>";
 echo $row['dbtime'];
 echo "</br>";
 echo $row['dbrpm'];
 echo "</br>";
 echo $row['dbmph'];
 echo "</br>";
 echo $row['dbthrottle'];
 echo "</br>";
 echo $row['dbload'];
 echo "</br>";
 echo $row['dbfuel'];
 echo "</br>";*/
 
 echo json_encode($row);
 
 //sleep(2);
 
?>
 
<?php
//Step5
 mysql_close($db);
?>
