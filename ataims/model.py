from typing import List, Optional, Set

from pydantic import BaseModel, Field


def dump(self, *args, **kwargs):
    return self.model_dump_json(*args, **kwargs)


BaseModel.dump = dump


class Results(BaseModel):
    total_energy:            float = Field(..., alias="Total Energy (eV)")
    fermi_energy:            float = Field(..., alias="Fermi Energy (eV)")
    highest_occupied_state:  float = Field(..., alias="Highest occupied state (eV)")
    lowest_unoccupied_state: float = Field(..., alias="Lowest unoccupied state (eV)")
    estimated_homo_lumo_gap: float = Field(..., alias="Estimated HOMO-LUMO gap (eV)")
    cell_volume:             float = Field(..., alias="Cell Volume (&#197;<sup>3</sup>)")


class CalculationSummary(BaseModel):
    code_version:                           str
    commit_number:                          str
    number_of_tasks:                        int
    total_time:                             float
    peak_memory_among_tasks_mb:             float
    largest_tracked_array_allocation_mb:    Optional[float]
    calculation_exited_regularly:           str


class DataSeries(BaseModel):
    data:  List[float]
    label: str  # Change of Eigenvalues, totalEnergy, chargeDensity...


class ChangeOfSumOfEigenvalues(BaseModel):
    charge_density:         Optional[DataSeries] = Field(None, alias="chargeDensity")
    charge_density_up:      Optional[DataSeries] = Field(None, alias="chargeDensityUp")
    charge_density_down:    Optional[DataSeries] = Field(None, alias="chargeDensityDown")
    eigen_values:           DataSeries = Field(..., alias="eigenvalues")
    total_energy:           DataSeries = Field(..., alias="totalEnergy")


class MaximumForceComponent(BaseModel):
    energy: DataSeries
    forces: DataSeries


class OutputData(BaseModel):
    """ GIMS OutputAnalyzer data model """
    results:                         Results
    calculation_summary:             CalculationSummary
    change_of_sum_of_eigenvalues:    List[ChangeOfSumOfEigenvalues]
    maximum_force_component:         Optional[MaximumForceComponent]
