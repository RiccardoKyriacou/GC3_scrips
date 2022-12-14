#!/usr/bin/env python3
from distutils.command.build_scripts import first_line_re
import glob
import argparse
import statistics
from Bio import SeqIO
from collections import defaultdict

'''
Script to calculate GC3 content per
chromosome/scaffold in a genome with
a given cutoff size. Able to use cds 
and primary tenplate data
'''

parse = argparse.ArgumentParser()

parse.add_argument("-p", "--path",type=str, help="path to genome fasta files",required=True)
parse.add_argument("-c", "--cutoff",type=int, help="cutoff for GC3 to be included as outliers ",required=True)
parse.add_argument("-o", "--outfile",type=str, help="name of output file",required=True)
parse.add_argument("-i", "--info",type=str, help="tsv file with species phylum information",required=False)
parse.add_argument("-n", "--nucleotides",type=int, help="amount of nucleotides allowed for outlier genes", required=False)

args = parse.parse_args()

#If species-clade info file provided, store data
if args.info:
    sp_names = {}
    sp_group = {}
    with open(args.info) as f:
        for line in f:
            lines = line.split('\t')
            species = lines[0]
            group = lines[1].strip()
            sp_group[species] = group

genome_list = []
for fasta in glob.glob(args.path + '*'):
    if fasta.endswith(('.fa', '.fasta', '.fas', '.fna')):
            genome_list.append(fasta)
print('Calculating GC3 content for', len(genome_list), 'genomes...\n')

outF = open(args.outfile, 'w')
outF1 = open("outlier_GC3_"+str(args.cutoff)+".tsv", 'w')

for fasta in glob.glob(args.path + '*'):
    if fasta.endswith(('.fa', '.fasta', '.fas', '.fna')):
        genome = fasta.split('/')[-1]
        sp_name = genome.split('.')[0].split('-')[0] # Lineus_longissimus-GCA_910592395.2-2022_03-cds.fa
        if args.info:
            group = sp_group[sp_name]

        chr_cds_seq = defaultdict(list)
        print(sp_name)
        with open(fasta) as f:
            first_line = f.readline()
            if ' ' in first_line:
                continue
            else:
                cds_path = args.path.split('primary')[0]
                cds_file = glob.glob(cds_path + genome)
                cds_file = cds_file[0]
                geneID_header = {}
                with open(cds_file) as f1:
                    for record in SeqIO.parse(f1, 'fasta'):
                        header = record.description
                        geneID = header.split(' ')[3].split(':')[1]
                        geneID_header[geneID] = header


            for record in SeqIO.parse(f, 'fasta'):
                header = record.description
                try:
                    chrom = header.split(':')[1]
                    chrom_info = header.split(" ")[2].split(":")[1:4]
                    chrom_info = ":".join(chrom_info)
                except:
                    chrom_full = geneID_header[header]
                    chrom = chrom_full.split(':')[1]
                    chrom_info = chrom_full.split(" ")[2].split(":")[1:4]
                    chrom_info = ":".join(chrom_info)

                seq = str(record.seq)
                seq_len = len(seq)
                transcript = record.id
               
                GC3 = seq[2::3] #Caculating GC3 

                GC3_count = GC3.count('G') + GC3.count('g') + GC3.count('C') + GC3.count('c')#Counting GC content to find cutoff
                GC3_len = len(GC3) 
                GC_content = (GC3_count/GC3_len)*100
                if (seq_len > args.nucleotides) and (GC_content > args.cutoff): #Looking cutooff of 950 3rd codon positions, not nucelotides
                    if seq.startswith("ATG"):
                        outF1.write(sp_name + "\t" + header + "_" + chrom_info  + "\n")
                    else:
                        outF1.write(sp_name + "\t" + header + "_" + chrom_info + "\t" + " No_ATG_StartCodon" + "\n")

                chr_cds_seq[chrom].append(GC3)#Append all cds sequences to each chromosome in a dictionary


        for chrm, cds_regions in chr_cds_seq.items():#For each chromosome and all cds sequences in the dictionary
            cds_joined = ''.join(cds_regions)#Join all cds sequences for a given chromosome into one big sequence
            len_cds_region = len(cds_joined)
            number_genes = len(cds_regions)
            GC3_count = cds_joined.count('G') + cds_joined.count('g') + cds_joined.count('C') + cds_joined.count('c')
            GC_content = (GC3_count/len_cds_region)*100

            outF.write(sp_name + '\t' + group + '\t' + str(len_cds_region) + '\t' + str(GC_content) + '\t' + str(number_genes) +'\n')

