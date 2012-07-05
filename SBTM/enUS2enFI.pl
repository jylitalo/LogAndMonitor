#
# Convert files from US settings into Finland's regional settings so that Excel can do calculations.
# Arguments:
# 1st argument is input directory (for example c:\sessions\reports)
#
 
$reportdir = shift @ARGV;
@filenames = ("","-coverage-sessions","-coverage-total","-day","-tester-day","-testers-sessions","-testers-total");
foreach $fname (@filenames) {
	$inputfile = "breakdowns${fname}.txt";
	$outputfile = "breadowns${fname}_en_FI.txt";
	open(FIN,"<$inputfile") || die "Can't open $inputfile for reading.";
	open(FOUT,">$outputfile") || die "Can't open $outputfile for writing.";
	while (<FIN>) {
		$data = $_;
		$data =~ tr/\./,/;
		print FOUT $data;
	} # while 
	close(FOUT);
	close(FIN);
	unlink($inputfile);
	rename($outputfile,$inputfile);
} # foreach
