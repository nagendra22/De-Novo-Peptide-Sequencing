# convert_mzml_to_mgf.ps1
# Converts mzML files to MGF for the de novo sequencing pipeline.

$conversions = @(
    # E. coli
    @{ Input = "data\ecoli\Ecoli_EV_1.mzML";                  OutDir = ".\data_mgf\ecoli";       OutFile = "Ecoli_EV_1.mgf" }
    @{ Input = "data\ecoli\Ecoli_EV_2.mzML";                  OutDir = ".\data_mgf\ecoli";       OutFile = "Ecoli_EV_2.mgf" }

    # Wastewater
    @{ Input = "data\wastewater\wastewater_Sample1_1.mzML";   OutDir = ".\data_mgf\wastewater";  OutFile = "wastewater_Sample1_1.mgf" }
    @{ Input = "data\wastewater\wastewater_Sample1_2.mzML";   OutDir = ".\data_mgf\wastewater";  OutFile = "wastewater_Sample1_2.mgf" }
    @{ Input = "data\wastewater\wastewater_Sample2_1.mzML";   OutDir = ".\data_mgf\wastewater";  OutFile = "wastewater_Sample2_1.mgf" }
    @{ Input = "data\wastewater\wastewater_Sample2_2.mzML";   OutDir = ".\data_mgf\wastewater";  OutFile = "wastewater_Sample2_2.mgf" }
)

foreach ($c in $conversions) {
    msconvert $c.Input --mgf `
        --filter "peakPicking true 1-2" `
        --filter "titleMaker <RunId>.<Index>.<ScanNumber>.<ChargeState>" `
        --outdir $c.OutDir `
        --outfile $c.OutFile
}