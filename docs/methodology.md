# Analysis Methodology

## Measurement model

For an unwrapped interferometric phase difference `phi`, the line-of-sight displacement is

```text
d_LOS = s lambda phi / 4 pi
```

where `lambda` is the radar wavelength and `s` is the documented sign convention. The software defaults to `s = -1`. LOS displacement is a projection onto the sensor look vector and must not be labelled as vertical displacement without additional geometry or decomposition.

## Quality filtering

The pipeline validates coordinates, finite numeric values and coherence bounds before analysis. It then applies the user-selected coherence threshold. A scaled median absolute deviation rule identifies extreme displacement outliers. This robust filter is intended to catch isolated processing artefacts; users should inspect removed points and avoid filtering coherent, physically plausible deformation gradients.

## Phase-noise precision

The reported coherence-derived precision uses the approximation

```text
sigma_phi = sqrt((1 - gamma^2) / (2 L gamma^2))
sigma_LOS = lambda sigma_phi / 4 pi
```

where `gamma` is coherence and `L` is the effective number of independent looks. This term describes phase-noise precision only. It does not include atmospheric delay, residual orbit error, DEM error, reference-frame uncertainty, decorrelation bias or phase-unwrapping error.

## Cross-fault profile

Observations are grouped by signed distance to the supplied fault trace. Each distance bin reports the mean LOS displacement, mean coherence, observation count and a percentile bootstrap interval for the mean. Bootstrap resampling is deterministic for reproducible tests. Spatial autocorrelation means the interval should not be interpreted as a complete geophysical confidence interval.

## Orbital ramp correction

The library provides coherence-weighted least-squares estimation of a planar ramp:

```text
z = a + b (longitude - longitude_0) + c (latitude - latitude_0)
```

Only independently justified, stable reference pixels should be used to estimate the plane. Fitting the ramp across a deforming area can remove real long-wavelength motion, so ramp removal is an explicit library operation rather than a default CLI step.

## Reproducibility

The demonstration generator and bootstrap procedure use fixed random seeds. A real analysis should retain the completed metadata record in `config/example_run_metadata.json`, source product identifiers, software versions, parameters, masks and validation evidence.

## References

1. ESA, *Sentinel-1 Toolbox TOPSAR Interferometry Tutorial*. https://step.esa.int/docs/tutorials/S1TBX%20TOPSAR%20Interferometry%20with%20Sentinel-1%20Tutorial_v2.pdf
2. Copernicus, *Sentinel-1 Products and Technical Documentation*. https://sentiwiki.copernicus.eu/web/s1-products
3. NASA ARIA, *Interferometric SAR displacement product guidance*. https://aria.jpl.nasa.gov/

