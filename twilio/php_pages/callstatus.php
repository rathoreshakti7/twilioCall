<?php
if(!isset($_REQUEST['key']) || empty($_REQUEST['key']) || $_REQUEST['key'] != 'JioBotqazQAZ') {
  header('X-Metric-App"');
  header('HTTP/1.0 401 Unauthorized');
  echo 'You are not authorized to acccess this application, Please contact Administrator';
  exit;
}
// page located at http://example.com/process_gather.php
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
echo "<Response><Say>Call status " . $_REQUEST['CallStatus'] . "</Say>";
echo "<Say>Key  " . $_REQUEST['key'] . "</Say>";
echo "<Say>  sessId  " . $_REQUEST['sessId'] . "</Say></Response>";

$myfile = fopen("/usr/share/nginx/html/callstatus.txt", "a") or die("Unable to open file!");
$txt = "Call status " . $_REQUEST['CallStatus'] . " key :" . $_REQUEST['key'] . " sessId : " . $_REQUEST['sessId'] . " done ";
fwrite($myfile, "\n". $txt);
fclose($myfile);
$callStatus = $_REQUEST['CallStatus'];
$sessionId = $_REQUEST['sessId'];
exec('curl -X PUT x.x.x.x:8500/v1/kv/app/phone_alert/call_tracker/' . $sessionId . '/status -d ' . $callStatus);
?>
