/*Sources
  seatbelt = ../Seatbelt.exe
Sources*/

function is_running(process_name)
{
	var t = seatbelt("Processes -full");
	const lines = t.split(/\r?\n/).filter(function(element) {return element;}); 
	for (j = 0; j < lines.length; j++) {
		if (lines[j].indexOf(process_name) > 0) {
		  print(lines[j]);
		  return true;
		}
	}
	return false;
}

for (i = 0; i < 10; i++) {
	sleep(5);
	if (is_running("NETSTAT")) {
		print(seatbelt("DNSCache"));
		break;
	}
}
