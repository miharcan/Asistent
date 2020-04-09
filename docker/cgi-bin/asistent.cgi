#!/usr/bin/perl
#mihael.arcan@deri.org

use strict;
use warnings;
use Data::Dumper;
use Benchmark;
use Locale::Codes::Language;

$ENV{'USER'} =  'www-data';

use utf8;
#binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");

use CGI::Carp qw(warningsToBrowser fatalsToBrowser);
use CGI::Carp qw(carpout);


my $t0 = new Benchmark;

use URI::Escape;
use File::Temp qw/ tempfile tempdir /;


my $moses_dir = "/home/tools/mosesdecoder";
my $home_dir = "/var/www/models"; ### current / test ### once
my $moses_ini = "moses.filtered.compact.tuned.ini";

my $dir = tempdir(DIR => "/tmp", CLEANUP =>  0 );
`mkdir $dir -p`;
`chmod -R 777 $dir`;

#open(my $log, ">>$dir/cgi.log") or die("Unable to open cgi.log: $!\n");
#carpout($log);

my @list;
read(STDIN, my $entry, $ENV{'CONTENT_LENGTH'});


my ($l1, $l2) = $entry =~ /name="direction"\s+(..)_(..)\r\n----/s;
my ($method) = $entry =~ /name="method"\s+(.+?)\r\n----/s;
my ($approach) = $entry =~ /name="approach"\s+(.+?)\r\n----/s;
my ($text) = $entry =~ /form-data; name="Text"\s(.*?)\r\n----/s;
$text =~ s/^\s+//;


my $selec_text;
if ($text =~ /^A delegated act adopted pursuant to Article 8 shall enter into force only if no objection has been expressed either by the European Parliament or the Council within a period of two months of notification of that act to the European Parliament and the Council or if, before the expiry of that period, the European Parliament and the Council have both informed the Commission that they will not object./) {
	$selec_text = "en";
} elsif ($text =~ /^NaloÅ¾ba je stala dobrih Å¡est milijonov evrov, polovico denarja je zagotovila Evropska unija, ostalo bolniÅ¡nica in drÅ¾ava. Center je Å¾e povsem opremljen, prve bolnike pa bo â zaradi administrativnih ovir â lahko sprejel Å¡ele februarja, je poroÄala novinarka TV Slovenija Ksenija Äernuta./) {
	$selec_text = "sl";
} elsif ($text =~ /^Kompanija Spejs iks lansirala je i uspeÅ¡no vertikalno prizemljila raketu Falkon 9, Å¡to se smatra vaÅ¾nom prekretnicom u nastojanjima da se smanje troÅ¡kovi viÅ¡ekratnim upotrebama raketa./) {
	$selec_text = "sr";
} elsif ($text =~ /^Direktorica sajma Magdalena Vodopija posebno je zahvalila organizacijskom timu, a ovogodiÅ¡nji je sajam posvetila svim hrvatskim nakladnicima koji su, kako je rekla, ove godine imali jako teÅ¡ku zadaÄu i unatoÄ velikim teÅ¡koÄama ostavili divne knjige, zauvijek./) {
	$selec_text = "hr";
} else {
	$selec_text = "unk";
}

print "Content-type: text/html\n\n";
my $header = <<"END_MESSAGE";
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8" />
		<title>ASISTENT | English-Slavic Translation System</title>
		<link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/font-awesome/4.3.0/css/font-awesome.min.css">
		<link rel="stylesheet" href="../style.css" />
		<link rel="stylesheet" href="../asistent.css" />

		<!--[if IE]>
		<script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script>
		<![endif]-->
	</head>
	<body>
		<header>
			<div class="container">
				<div class="alighleft">
					<span class="logo"><span class="green">ASISTENT</span></span>
					English-Slavic Translation System
				</div>
				<ul class="alighright">
					<li><a href="../"><i class="fa fa-home"></i> Home</a></li>
					<li><a href="../about.html"><i class="fa fa-comment"></i> About</a></li>
					<li><a href="../team.html"><i class="fa fa-users"></i> Team</a></li>
					<li><a href="../rest_service.html"><i class="fa fa-cogs"></i> API</a></li>
					<li><a href="../txt_upload.html"><i class="fa fa-file-code-o"></i> TXT Upload</a></li>
					<li>
						<a href="#"><i class="fa fa-tags"></i> Other Projects</a>
						<ul>
							<li><a href="../../iris/" target="_top">IRIS</a></li>
							<li><a href="../../otto/" target="_top">OTTO</a></li>
							<li><a href="../../asistent/" target="_top">ASISTENT</a></li>
							<li><a href="../../tetra/" target="_top">TeTra</a></li>
						</ul>
					</li>
				</ul>
				<div class="clear"></div>
			</div>
		</header>
		<div class="container">
			<div class="contentsfull">
END_MESSAGE
print $header;


#print "$entry\n<br><br>"; ###exit;
#print "|$l1|$l2|$method|$approach|$text|$selec_text"; exit;


if ($selec_text ne "unk") {
	if ($l1 ne $selec_text) {
		print "The language of the selected text and translation direction do not match. Please select again.<br><br>";
		print "<div style=\"text-align: center\"><a href=\"../\" TARGET=\"_top\"><strong>Back to homepage</strong></strong</a></div>";
		exit;
	} else {
#		print "Languages match - will continue";
	}
}

my $nbf_cgi = "$dir/nbestlist.txt";

my $sa = 1;
if ($method eq "hierarchical") {
	$sa = 3;
	$home_dir = "/var/www/models";
	$moses_ini = "moses.filtered.ondisk.tuned.ini";
}

if (($text)) {
	$text =~ s/\n\r/\n/g;
	$text =~ s/\.\s/.\n/g if ($method eq "nmt");
	$text =~ s/(\n\r)+/\n/g;
	@{$list[0]} = split(/\n+/,$text);
	my $cpus = scalar (@{$list[0]});
	if (scalar (@{$list[0]}) > 4) {
		$cpus = 4;
	}
	foreach my $i (0 .. $#{$list[0]}) {
		$list[0][$i] =~ s/\+/ /g;
		$list[0][$i]  = uri_unescape($list[0][$i]);
	}
	my $string = join("\n",@{$list[0]});
	$string =~ s/"/'/g;
	$string =~ s/'/\'/g;

	if (scalar(@{$list[0]}) < 250) {
		if ($approach eq "direct") {
			unless ($method eq "nmt") {
				unless (-f "/var/www/models/$method/$l1\_$l2/model/moses.ini") {
		            `wget http://server1.nlp.insight-centre.org/mt_models/$method/models_$l1\_$l2\.tgz -O /var/www/models/$method/models_$l1\_$l2\.tgz` unless (-f "/var/www/models/$method/models_$l1\_$l2\.tgz");
		            `mkdir -p /var/www/models/$method/$l1\_$l2/model`;
		            `tar xfz /var/www/models/$method/models_$l1\_$l2\.tgz -C /var/www/models/$method/$l1\_$l2/model/` unless (-f "/var/www/models/$method/$l1\_$l2/model/moses.ini");
                }
                open my $in, "<", "/var/www/models/$method/$l1\_$l2/model/moses.ini";
                undef $/; my $file=<$in>; $/ = "\n";
                close($in);
                `cp /var/www/models/$method/$l1\_$l2/model/moses.ini /var/www/models/$method/$l1\_$l2/model/moses.ini.bak`;
                $file =~ s/phrase-table-filtered-compact/phrase-table/;
                $file =~ s/\/home\/miharc\/ssd\/translation_models\/generic/\/var\/www\/models\/$method/;
                $file =~ s/\/home\/mosesdecoder\/models\/$l1\_$l2/\/var\/www\/models\/$method\/$l1\_$l2\/model/g;
                open my $out, ">", "/var/www/models/$method/$l1\_$l2/model/$moses_ini";
                print $out $file;
                close($out);
				@{$list[2]} = `echo "$string" | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -n-best-list $dir/nbestlist.txt 25 distinct -v 0 -threads $cpus | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`; ##### | tee > $home_dir/translations/$rand/translations.lc.txt
			} elsif ($method eq "nmt") {
				unless (-f "/var/www/models/nmt/$l1\_$l2\_bpe32k_brnn_freq3_len80_epoch13_release.t7") {
		            `wget http://server1.nlp.insight-centre.org/mt_models/nmt/$l1\_$l2\_bpe32k_brnn_freq3_len80_epoch13_release.t7 -O /var/www/models/nmt/$l1\_$l2\_bpe32k_brnn_freq3_len80_epoch13_release.t7`;
		            `wget http://server1.nlp.insight-centre.org/mt_models/nmt/$l1.bpe32k -O /var/www/models/bpes/$l1.bpe32k.model`;
                }
				@{$list[2]} = `echo "$string" | $moses_dir/scripts/tokenizer/lowercase.perl | /home/tools/CTranslate/lib/tokenizer/build/cli/tokenize --mode aggressive --bpe_model /var/www/models/bpes/$l1.bpe32k.model --joiner_annotate | /home/tools/CTranslate/build/cli/translate --model /var/www/models/nmt/$l1\_$l2\_bpe32k_brnn_freq3_len80_epoch13_release.t7 --threads 4 | /home/tools/CTranslate/lib/tokenizer/build/cli/detokenize | $moses_dir/scripts/tokenizer/tokenizer.perl | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`;
			}
		} elsif ($approach eq "pivot") {
			my %langs; $langs{"sl"}=0; $langs{"sr"}=0; $langs{"hr"}=0; $langs{"en"}=0;
			my @temps; push(@temps,$l1,$l2);
			foreach my $l (@temps) {
				delete($langs{$l});
			}
			if ($method eq "nmt") {
#				print "Dear User, pivot translation is not supported for NMT yet."; 
#				exit;
				foreach my $pivot (keys %langs) {
					@{$list[2]} = `echo "$string" | $moses_dir/scripts/tokenizer/lowercase.perl | /home/tools/CTranslate/lib/tokenizer/build/cli/tokenize --mode aggressive --bpe_model /var/www/models/bpes/$l1.bpe32k.model --joiner_annotate | /home/tools/CTranslate/build/cli/translate --model /var/www/models/nmt/$l1\_$pivot\_bpe32k_brnn_freq3_len80_epoch13_release.t7 --threads 4 | /home/tools/CTranslate/build/cli/translate --model /var/www/models/nmt/$pivot\_$l2\_bpe32k_brnn_freq3_len80_epoch13_release.t7 --threads 4 | /home/tools/CTranslate/lib/tokenizer/build/cli/detokenize | $moses_dir/scripts/tokenizer/tokenizer.perl | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`;  ###> $dir/nmt_$l1\_$pivot\_$l2.txt
					last;
				}
			} else {
				my %tmp;
				my %nb_tmp;
				foreach my $pivot (keys %langs) {
					`echo "$string" | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$pivot/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$pivot\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus -n-best-list $dir/nbestlist_$pivot.txt 25 distinct`;
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
				}
				foreach my $id (sort keys %tmp) {
					$list[2][$id]= `echo "$tmp{$id}{best_sent}" | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`;
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
		}

		print "<table  width=\"100%\" border=\"0\">\n";
		my $width = "40";
		print "<tr><td width=\"$width%\" style=\"text-align:center\"><b>Source language</b></td><td width=\"4%\"></td><td width=\"$width%\" style=\"text-align:center\"><b>Target language</b></td><td style=\"text-align:right\"><b>Optional transl.</b></td></tr>\n";

		print "</table>\n";
		print "<hr style=\"color:#FFFFFF;\">\n";
		print "<table width=\"100%\" border=\"0\">\n";
	
	
		my $size = 1;
		my $last = $#{$list[0]};
		foreach my $i (0 .. $#{$list[0]}) {
			if ($list[0][$i]) {
				$size++ if ($last == $i);
				$list[0][$i] =~ s/(\n|\r|\x0d)//g;
				$list[2][$i] =~ s/(\n|\r|\x0d)//g;
				$list[2][$i] =~ s/\s*\@-\@\s*/-/g;
				my $target = $list[2][$i];
				my $source = $list[0][$i];
				use Encode;
				utf8::decode($target);
				utf8::decode($source);
				
				
				unless ($method eq "nmt") {
			
				print "<tr><td width=\"$width%\" style=\"text-align:justify\">$source</td><td width=\"4%\"><div style=\"text-align: center\">&#8594;</div></td><td width=\"$width%\" style=\"text-align:justify\">$target</td><td width=\"2%\"></td><td width=\"5%\">
						
				
						<form method=\"post\" action=\"get_n_best.cgi\" target=\"_blank\">
						<input type=\"submit\" name =\"$list[0][$i]|||$i|||$nbf_cgi\"  value=\"n-best\" >
						</form>
						</td>
						</tr><tr><td colspan=\"5\"><hr style=\"color:#FFFFFF;\" SIZE=\"$size\"></td></tr>\n"; 
				} else {
					print "<tr><td width=\"$width%\" style=\"text-align:justify\">$source</td><td width=\"4%\"><div style=\"text-align: center\">&#8594;</div></td><td width=\"$width%\" style=\"text-align:justify\">$target</td><td width=\"2%\"></td><td width=\"5%\">
						</td>
						</tr><tr><td colspan=\"5\"><hr style=\"color:#FFFFFF;\" SIZE=\"$size\"></td></tr>\n"; 
				}
				
			}
		}
		my ($time) = timestr(timediff(new Benchmark, $t0)) =~ /(\d+) wallclock secs/;
		print "</table>\n";
		my $lang1 = code2language($l1);
		my $lang2 = code2language($l2);
#		print "<hr style=\"color:#FFFFFF;\">\n";
		print "<font size=\"2\">\n";
		print "<div style=\"text-align: center\">decoding took $time seconds (L1=$lang1,L2=$lang2,method=$method,approach=$approach)</div>\n";
		
		print "</font>\n";
		print "<br>\n";
	} else {
		print "Due to the reserach environment, please reduce the data to be translated to 200 sentences. Please contact <a href=\"mailto:mihael.arcan\@insight-centre.org\">Mihael Arcan</a>, if you need to translate a larger amount of text. <br><br>\n";
	}
} else {
	print "No text was added<br>";
}



print "<div style=\"text-align: center\"><a href=\"../\" TARGET=\"_top\"><strong>Back to homepage</strong></strong</a></div>";
print <<"END_MESSAGE";
			</div>
		</div>
	</body>
</html>
END_MESSAGE


