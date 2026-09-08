# Sentinel-1 DInSAR Processing Notes

## Scope

This repository focuses on analysis after phase unwrapping and geocoding. It does not distribute Sentinel-1 scenes, DEM tiles or derived products from a real event. Those inputs are large and may carry attribution or redistribution requirements.

## Recommended upstream workflow

### Scene selection

Select Sentinel-1 SLC scenes with the same relative orbit, acquisition mode, subswath and polarisation. Keep the temporal and perpendicular baselines appropriate for the land cover and event being studied.

### Co-registration and interferogram formation

Apply precise orbit files, split the required TOPS subswath and co-register the pair using back-geocoding. Form the differential interferogram and deburst before multilooking or spatial filtering where appropriate.

### Topographic phase and filtering

Remove simulated topographic phase using a documented DEM. Record DEM source and resolution. Apply Goldstein filtering only with parameters retained in the run metadata, because filtering changes the spatial detail available for interpretation.

### Phase unwrapping

Export the wrapped phase and coherence to SNAPHU. Inspect connected components and discontinuities rather than treating successful software execution as proof of a valid unwrap.

### Displacement and terrain correction

Convert unwrapped phase to line-of-sight displacement using the correct radar wavelength and sign convention. Terrain-correct the product, retain the map projection and export coherence alongside displacement.

## Interpretation safeguards

- LOS displacement is not automatically vertical displacement.
- Atmospheric delay, orbital ramps, ionospheric effects and DEM errors can resemble deformation.
- Vegetation, snow, water and long temporal baselines can reduce coherence.
- Strong displacement gradients can exceed the phase-unwrapping capacity.
- Masked or interpolated pixels must be distinguished from observed values.
- Validate against GNSS, independent interferograms or published products where possible.

## Provenance checklist

For a real case study, record:

- Sentinel-1 product identifiers and acquisition dates;
- ascending or descending orbit and relative orbit number;
- polarisation and subswath;
- temporal and perpendicular baselines;
- DEM source;
- filtering and multilooking parameters;
- SNAPHU mode and unwrapping parameters;
- coherence threshold and masks;
- projection, pixel spacing and sign convention;
- validation source and limitations.

Use `config/example_run_metadata.json` as the machine-readable record for these fields. The statistical assumptions and equations used by the Python package are documented in `docs/methodology.md`.
