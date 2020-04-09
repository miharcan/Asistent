#!/usr/bin/perl
#mihael.arcan@deri.org

use strict;
use warnings;
use Data::Dumper;
use Benchmark;
$Data::Dumper::Useperl = 1;

use Storable;
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);

use JSON;
use Encode qw(encode_utf8);
use URI::Escape;
use utf8;
#binmode(STDIN, ":utf8");
#binmode(STDOUT, ":utf8");

my $t0 = new Benchmark;

print "Content-type:application/json\r\n\r\n";
my $moses_dir = "/home/miharc/mosesdecoder_2016_08";
my $home_dir = "/home/miharc/ssd/translation_models"; ### current / test ### once
my $moses_ini = "moses.filtered.compact.tuned.ini";


use File::Temp qw/ tempfile tempdir /;
my $dir = tempdir(DIR => "/home/miharc/demos/asistent/temp/", CLEANUP =>  0 );
`mkdir -p $dir`;
`chmod -R 777 $dir/`;

use CGI::Carp qw(warningsToBrowser fatalsToBrowser);
use CGI::Carp qw(carpout);
open(my $log, ">>$dir/cgi.log") or die("Unable to open mycgi.log: $!\n");
carpout($log);

my ($buffer, @list, %hash);
# Read in text    
$ENV{'REQUEST_METHOD'} =~ tr/a-z/A-Z/;    
if ($ENV{'REQUEST_METHOD'} eq "GET"){
	$buffer = $ENV{'QUERY_STRING'};
}
$buffer  = uri_unescape($buffer);

my %keys;
$keys{oogh6EeH5uonugho}=1; ### unlp key
$keys{ahTh7xeechaK9Ba5}=1; ### maja probably

open my $file, ">:utf8", "$dir/test" or die;
print $file $buffer;
my ($json) = $buffer =~ /^json=({.+?})$/;
print $file "\n$json\n";
my %data = %{ from_json ($json, {utf8 => 1}) };

my $cpu = 1;
my $sleep = 5;

#my @sentences = $data{string2translate};
#my $string = join("\n", @sentence);
#my $string;
my $string; #= join("\n", @{$data{string2translate}});
my $method = $data{"method"};
$method = "generic" unless ($method eq "nmt");
my $approach = $data{"approach"};
print $file Dumper \%data;


foreach my $i (0 .. $#{$data{text2translate}}) {
	$string .= "$data{text2translate}[$i]{source}\n";
}

my $ldirec = $data{translation_direction};
my ($l1, $l2) = $ldirec =~ /^(..)_(..)$/;
my $key = $data{key};
if ($key and (exists ($keys{$key}))) {
	$cpu = 4;
	$sleep = 0;
} else {
	$data{key} = "Could not recognise key - the translation was performed with lowest priority.";
}



#utf8::decode{$string};
$string =~ s/"/'/g;
$string =~ s/'/\'/g;
chomp($string);


my $sa = 1;
if ($method eq "hierarchical") {
	$sa = 3;
	$home_dir = "/home/miharc/translation_models";
	$moses_ini = "moses.filtered.ondisk.tuned.ini";
}


if (($string)) { ####&&($lang_id)
	$string =~ s/\n\r/\n/g;
	@{$list[0]} = split(/\n+/,$string);
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
				@{$list[2]} = `echo "$string" | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -n-best-list $dir/nbestlist.txt $data{nbest} distinct -v 0 -threads $cpus | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`; 
				##### | tee > $home_dir/translations/$rand/translations.lc.txt
			} else {
				@{$list[2]} = `echo "$string" | $moses_dir/scripts/tokenizer/lowercase.perl | /home/miharc/public_html/cgi-bin/tools/tokenize --mode aggressive --bpe_model /home/miharc/translation_models/bpes/$l1.bpe32k --joiner_annotate | /home/miharc/public_html/cgi-bin/tools/translate --model /home/miharc/ssd/translation_models/nmt/asistent/$l1\_$l2\_bpe32k_brnn_freq3_len80_epoch13_release.t7 --threads 4 | /home/miharc/public_html/cgi-bin/tools/detokenize | $moses_dir/scripts/tokenizer/tokenizer.perl | nice ionice -c 2 -n 0 $moses_dir/scripts/tokenizer/detokenizer.perl -u -l $l2 -threads $cpus`;
				foreach my $i (0 .. $#{$list[2]}) {
					chomp($list[2][$i]);
#					utf8::decode{$list[2][$i]};
					$data{text2translate}[$i]{best_translation} = $list[2][$i];
				}
				delete($data{nbest});
			}
		} elsif ($approach eq "pivot") {
			if ($method eq "nmt") {
				$data{text2translate}[0]{best_translation} = "Dear User, pivot translation is not supported for NMT yet.";
			} else {
				my %langs; $langs{"sl"}=0; $langs{"sr"}=0; $langs{"hr"}=0; $langs{"en"}=0;
				my @temps; push(@temps,$l1,$l2);
				foreach my $l (@temps) {
					delete($langs{$l});
				}
				my %tmp;
				my %nb_tmp;
				foreach my $pivot (keys %langs) {
					@{$list[1]} = `echo "$string" | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/tokenizer.perl -a -threads $cpus -l $l1 | nice -n 4 ionice -c 2 -n 0 perl $moses_dir/scripts/tokenizer/lowercase.perl | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$l1\_$pivot/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus | nice -n 4 ionice -c 2 -n 0 $moses_dir/bin/moses -f $home_dir/$method/$pivot\_$l2/model/$moses_ini -search-algorithm $sa -cube-pruning-pop-limit 500 -s 500 -v 0 -threads $cpus -n-best-list $dir/nbestlist_$pivot.txt $data{nbest} distinct`;
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
	}
}

`sleep $sleep`;


#$hash{translation_direction} = $ldirec;
unless ($method eq "nmt") {
open my $nbf, "<:utf8", "$dir/nbestlist.txt" or die "error nbest $!\n";
my $i = 0;
my $x=0;
while (my $line =<$nbf>) {
	chomp($line);
	my ($id, $tr, $p) = $line =~ /^(\d+)\s\|\|\|\s(.+?)\s\|\|\|.+?\|\|\|\s(.+?)$/;
	if ($x != $id) {
		$i = 0;
		$x = $id;
	}
	if ($i==0) {
		$data{text2translate}[$id]{best_translation} = $tr;
		$i++;
	}
	utf8::decode{$tr};
	$data{text2translate}[$id]{possible_translations}{$tr}=$p;
	print $file "$id ||| $data{text2translate}[$id]{source} ||| $tr ||| $p\n"
}
}
$data{"time"}=timestr(timediff(new Benchmark, $t0));

#print $file Dumper \%hash; exit;

my $json_out = JSON->new->allow_nonref;
printf "%s\n", $json_out->encode(\%data);



