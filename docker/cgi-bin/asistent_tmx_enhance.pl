#!/usr/bin/perl

use strict;
use warnings;
use Data::Dumper;
#$Data::Dumper::Useperl = 1;
use Benchmark;
use utf8;
use URI::Escape;
use Encode;
use Locale::Codes::Language;
#binmode(STDIN, ":utf8");
#binmode(STDOUT, ":utf8");
use POSIX qw(strftime);
my $t = time;
my $cpus = 4;

my $moses_dir = "/home/miharc/mosesdecoder_2016_08";
my $home_dir = "/home/miharc/ssd/translation_models";
my $moses_ini = "moses.filtered.compact.tuned.ini";

my $dir = shift;
my $filename = shift;
my $tr_direc = shift;
my $method = shift;
my $approach = shift;
my $email = shift;

my $time = strftime "%FT%XZ", localtime;
##"2011-10-18T18:20:51Z

my ($fn, $fe) = $filename =~ /^(.+?)\.(tmx|txt)$/;

my ($l1, $l2) = $tr_direc =~ /^(..)_(..)$/;

open my $file_in, "<", "$dir/$filename" or die "err no file $!\n"; ##:utf8
open my $tmpfile, ">:utf8", "$dir/tmp.txt";
open my $file_out, ">", "$dir/sentences.txt";  ###:utf8

undef $/; my $data = <$file_in>; $/ = "\n";

my $type;
my $to_translate;

my %hash;

my $sa = 1;
if ($method eq "hierarchical") {
	$sa = 3;
	$home_dir = "/home/miharc/translation_models";
	$moses_ini = "moses.filtered.ondisk.tuned.ini";
}

if ($data =~ /<tmx version/) {
	$type = "TMX";
	tmxdata($data);
} else  {
	txtdata($data);
}

sub txtdata {
	$type = "TXT";
	my $txtdata = shift;

	$txtdata =~ s/"/'/g;
	$txtdata =~ s/'/\'/g;
#	$text =~ s/(\n\r)+/\n/g;

	print $file_out $txtdata;
	my @array = split(/\n+/,$txtdata);

	my @transl;
	if ($approach eq "direct") {
		unless ($method eq "nmt" ) {
			@transl = `nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 < $dir/sentences.txt | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -n-best-list $dir/nbestlist.txt 25 distinct -v 0 -threads $cpus | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`; ##### | tee > $home_dir/translations/$rand/translations.lc.txt
		} else {
			@transl = `$moses_dir/scripts/tokenizer/lowercase.perl < $dir/sentences.txt | /home/miharc/public_html/cgi-bin/tools/tokenize --mode aggressive --bpe_model /home/miharc/translation_models/bpes/$l1.bpe32k --joiner_annotate | /home/miharc/public_html/cgi-bin/tools/translate --model /home/miharc/ssd/translation_models/nmt/asistent/$l1\_$l2\_bpe32k_brnn_freq3_len80_epoch13_release.t7 --threads 4 | /home/miharc/public_html/cgi-bin/tools/detokenize | $moses_dir/scripts/tokenizer/tokenizer.perl | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`;
		}
	} elsif ($approach eq "pivot") {
		my %langs; $langs{"sl"}=0; $langs{"sr"}=0; $langs{"hr"}=0; $langs{"en"}=0;
		my @temps; push(@temps,$l1,$l2);
		foreach my $l (@temps) {
			delete($langs{$l});
		}
		my %tmp;
		my %nb_tmp;
		foreach my $pivot (keys %langs) {
			`nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 < $dir/sentences.txt | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$pivot/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$pivot\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus -n-best-list $dir/nbestlist_$pivot.txt 25 distinct`;
			open my $nbfile, "<:utf8", "$dir/nbestlist_$pivot.txt";
			while(my $line=<$nbfile>) {
				chomp($line);
				my ($id, $sent, $lm, $p) = $line =~ /^(\d+)\s*\|\|\|\s(.+?)\s\|\|\|.+?LM0=\s(.+?)\sWordPenalty0.+?\|\|\|\s(.+?)\s*$/;
				$nb_tmp{$id}{$lm}{$line}=$pivot;
				if (not exists($tmp{"$id"}{best_p})) {
					$tmp{$id}{best_p}=$lm;
					$tmp{$id}{best_sent}=$sent;
				} else {
					if ($lm > $tmp{$id}{best_p}) {
						$tmp{$id}{best_p}=$lm;
						$tmp{$id}{best_sent}=$sent;
					}
				}
			}
			`rm "$dir/nbestlist_$pivot.txt"`;
		}
		foreach my $id (sort keys %tmp) {
			$transl[$id]= `echo "$tmp{$id}{best_sent}" | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`;
		}
		open my $nb_final, ">:utf8", "$dir/nbestlist.txt";
		foreach my $id (sort {$a <=> $b} keys %nb_tmp) {
			foreach my $lmp (sort {$b <=> $a} keys %{$nb_tmp{$id}}) {
				foreach my $s (keys %{$nb_tmp{$id}{$lmp}}) {
					print $nb_final "$s\n";
				}
			}
		}
	}

	open my $final_out, ">:utf8", "$dir/$fn\_byAsistent.tmx" or die "err file translated $!\n"; ###:utf8 
	open my $final_out2, ">:utf8", "$dir/$fn\_byAsistent.1_2.xlf" or die "err file translated $!\n"; ###:utf8 
	open my $final_out3, ">:utf8", "$dir/$fn\_byAsistent.2_0.xlf" or die "err file translated $!\n"; ###:utf8 
	open my $final_out4, ">:utf8", "$dir/$fn\_byAsistent.txt" or die "err file translated $!\n"; ###:utf8 

	my $tmxheader = <<"END_MESSAGE";
<tmx version="1.4">
  <header
    creationtool="XYZTool" creationtoolversion="1.01-023"
    datatype="PlainText" segtype="sentence"
    adminlang="en-us" srclang="en"
    o-tmf="ABCTransMem"/>
  <body>
END_MESSAGE
	print $final_out $tmxheader;

	my $xliffheader = <<"END_MESSAGE";
<xliff version="1.2">
 <file original="$filename"
  source-language="$l1" target-language="$l2"
  tool="Asistent" datatype="plaintext">
  <header>
   <phase-group>
    <phase phase-name="extract" process-name="extraction"
     tool="Asistent" date="$time"
     company-name="NeverLand Inc." job-id="999"
     contact-name="Joe Dow" contact-email="joedoe\@example.com">
    </phase>
   </phase-group>
  </header>
  <body>
END_MESSAGE
	print $final_out2 $xliffheader;

	my $xliffheader2 = <<"END_MESSAGE";
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0"
 srcLang="$l1" trgLang="$l2">
 <file id="f1" original="Example">
END_MESSAGE
	print $final_out3 $xliffheader2;

	foreach my $i (0 .. $#array) {
		chomp($transl[$i]);
		utf8::decode($array[$i]);
		utf8::decode($transl[$i]);
		my $j = $i+1;
		### print txt
		print $final_out4 "$transl[$i]\n";
		###print tmx
		print $final_out "    <tu>\n      <tuv xml:lang=\"$l1\">\n        <seg>$array[$i]<\/seg>\n      </tuv>\n      <tuv xml:lang=\"$l2\">\n        <seg>$transl[$i]</seg>\n      </tuv>\n    </tu>\n";
		###print xliff1.2
		print $final_out2 "   <trans-unit id=\"$j\">\n    <source xml:lang=\"$l1\">$array[$i]</source>\n    <target xml:lang=\"$l2\">$transl[$i]</target>\n   </trans-unit>\n";
		###pritn xliff2.0
		print $final_out3 " <unit id=\"$j\">\n   <segment>\n    <source>$array[$i]</source>\n    <target>$transl[$i]</target>\n   </segment>\n  </unit>\n";
	}

	print $final_out "  </body>\n</tmx>";
	close($final_out);
	print $final_out2 "  </body>\n </file>\n</xliff>";
	close($final_out2);
	print $final_out3  " </file>\n</xliff>";
	close($final_out3);
	close($final_out4);
	
	`rm $dir/tmp.txt`;
	`rm $dir/sentences.txt`;
}

sub tmxdata {

	my $tmxdata = shift;
	my ($body) = $tmxdata =~ /(<body.+?<\/body>)/s;

	print $tmpfile "$body\n\n$tr_direc\n\n";
	
	my $j = 0;
	while ($body =~ /(<tu.+?<\/tu>)/sg) {
		my $tu = $1;
		print $tmpfile "\ntu\n$tu\n";
		while ($tu =~ /(<tuv.+?<\/tuv>)/sg) {
			my $tuv = $1;
			print $tmpfile "\ntuv\n$tuv\n";
			my ($lang) = $tuv =~ /xml:lang="(.+?)">/;
			if ((lc($lang) =~ /^$l1/i)&&($tu !~ /xml:lang="$l2/i)) {
				my ($sent) = $tuv =~ /seg>(.+?)<\/seg>/;
				$to_translate .= "$sent\n";
				$hash{$sent}=$j;
				$j++;
			}
		}
	}
	print $file_out "$to_translate";

	#my @transl = `nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 < $dir/sentences.txt | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/generic/$l1\_$l2/model/$moses_ini -v 0 -threads $cpus | /home/miharc/mosesdecoder_2016_08/scripts/tokenizer/detokenizer.perl`; ### > $dir/sentences_translated.txt
	
	my @transl;
	
	if ($approach eq "direct") {
		@transl = `nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 < $dir/sentences.txt | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`; ##### | tee > $home_dir/translations/$rand/translations.lc.txt #####-n-best-list $dir/nbestlist.txt 25 distinct
	} elsif ($approach eq "pivot") {
		my %langs; $langs{"sl"}=0; $langs{"sr"}=0; $langs{"hr"}=0; $langs{"en"}=0;
		my @temps; push(@temps,$l1,$l2);
		foreach my $l (@temps) {
			delete($langs{$l});
		}
		my %tmp;
		my %nb_tmp;
		foreach my $pivot (keys %langs) {
			@transl = `nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 < $dir/sentences.txt | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$pivot/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$pivot\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus`; ####  -n-best-list $dir/nbestlist_$pivot.txt 25 distinct
#			open my $nbfile, "<:utf8", "$dir/nbestlist_$pivot.txt";
#			while(my $line=<$nbfile>) {
#				chomp($line);
#				my ($id, $sent, $lm, $p) = $line =~ /^(\d+)\s*\|\|\|\s(.+?)\s\|\|\|.+?LM0=\s(.+?)\sWordPenalty0.+?\|\|\|\s(.+?)\s*$/;
#				$nb_tmp{$id}{$lm}{$line}=$pivot;
#				if (not exists($tmp{"$id"}{best_p})) {
#					$tmp{$id}{best_p}=$lm;
#					$tmp{$id}{best_sent}=$sent;
#				} else {
#					if ($lm > $tmp{$id}{best_p}) {
#						$tmp{$id}{best_p}=$lm;
#						$tmp{$id}{best_sent}=$sent;
#					}
#				}
#			}
		}
#		foreach my $id (sort keys %tmp) {
#			$list[2][$id]= `echo "$tmp{$id}{best_sent}" | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`;
#		}
#		open my $nb_final, ">:utf8", "$dir/nbestlist.txt";
#		foreach my $id (sort {$a <=> $b} keys %nb_tmp) {
#			foreach my $lmp (sort {$b <=> $a} keys %{$nb_tmp{$id}}) {
#				foreach my $s (keys %{$nb_tmp{$id}{$lmp}}) {
#					print $nb_final "$s\n"; ###delegirani akt sprejet na podlagi člena 8 , začne veljati le , če niti evropski parlament in svet uprejo v roku dveh mesecev od priopćenja , ki delujejo v evropskem parlamentu in svetu , ali če pred iztekom tega roka evropski parlament in svet obvestila komisijo , da se ne bo upirala
#				}
#			}
#		}
	}

	while ($body =~ /(<tu.+?<\/tu>)/sg) {
		my $tu = $1;
		print $tmpfile "\ntu2\n$tu\n";
		while ($tu =~ /\n(\s*)(<tuv.+?<\/tuv>)/sg) {
			my $tuv = $2;
			my $tuv_space = $1;
			print $tmpfile "\ntuv2\n$tuv\n";
			my ($lang) = $tuv =~ /xml:lang="(.+?)">/;
			if ((lc($lang) =~ /^$l1/i)&&($tu !~ /xml:lang="$l2/i)) {
				my ($seg_space, $sent) = $tuv =~ /\n(\s*)<seg>(.+?)<\/seg>/;
				if (exists($hash{$sent})) {
					chomp($transl[$hash{$sent}]);
					print $tmpfile "sent\n$sent|||$transl[$hash{$sent}]\n\n";
					my $modtuv = "$tuv\n$tuv_space<tuv xml:lang=\"$l2\">\n$seg_space<seg>$transl[$hash{$sent}]<\/seg>\n$tuv_space<\/tuv>";
					print $tmpfile "\ntuv_modtuv2\n||$tuv||\n||$modtuv||\n";
					$data =~ s/\Q$tuv\E/$modtuv/g;
					$tuv =~ s/\\([\(\)])/$1/g;
					print $tmpfile "\ndata2\n$data\n";
				}
			}
		}
	}
	`rm $dir/tmp.txt`;
	`rm $dir/sentences.txt`;
	open my $final_tmx, ">", "$dir/$fn\_byAsistent.tmx" or die "err file translated $!\n"; ###:utf8 
	print $final_tmx $data;
	close($final_tmx);
}


my $w3path = "http://server1.nlp.insight-centre.org/asistent";
my ($suffix, $code) = $dir =~ /.+?\/(temp)\/(.+?)$/; 
$w3path .= "/$suffix/$code";
if ($email) {
	use POSIX qw(strftime);	
	my $time = strftime "%X, %x", localtime;
	my $text = "Dear Asistent User,\n\nThe \"Asistent System\" finished (at $time) translating the $type file with the name: $filename.\n\nThe results are stored in $w3path.\n\nBest Regards,\nMihael Arcan";
	send_mail($text);
}

##########################
##########################
##########################

sub send_mail {
	my $message = shift;
	my $to = $email;
	my $from = 'mihael.arcan@insight-centre.org';
	my $subject = "Asistent System - FINISHED, file: $filename";
#	
	open(MAIL, "|/usr/sbin/sendmail -t");
	# Email Header
	print MAIL "To: $to\n";
	print MAIL "From: $from\n";
	print MAIL "Subject: $subject\n\n";
	# Email Body
	print MAIL $message;
	close(MAIL);
}



#open my $tr_file, "<:utf8", "$dir/sentences_translated.txt";
#my $i = 0;
#while (my $line = <$tr_file>) {
#	chomp($line);
#	print $tmpfile "\nline\n$line||\t$array[$i]\n";
##	my ($orgtuv) = $body =~ /\n(\s*<tuv.+?>\n\s*<seg>$array[$i]<\/seg>\n\s*<\/tuv>)\n/is;
#	my ($orgtuv) = $body =~ /\n(\s*<tuv.+?>\n\s*<seg>$array[$i]<\/seg>\n\s*<\/tuv>)/i;
#	print $tmpfile "\norgtuv\n$orgtuv\n";
#	my $modtuv = $orgtuv;
#	$modtuv =~ s/(<tuv.+?lang)=".+?"(.+?<seg>)$array[$i](<\/seg>.+?<\/tuv>)/$1="$l2"$2$line$3/igs;
#	$tmxdata =~ s/$orgtuv/$orgtuv\n$modtuv/gs;
#	print $tmpfile "\nmodtuv$modtuv\nbody\n$body\ntmxdata\n$tmxdata\n\n";
#	$i++;
#}
#print $tmpfile "\n\ntmx\n$tmxdata\n";
