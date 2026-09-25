# Siret3 vineyard map -- weekend plan

Marcaj is the scored source. Deadline Sunday 27 Sep 2026, 15:00 Chisinau. Full catalog: vineyard-research.md.

## Bet

Fine-tune Riseholme COCO to YOLO11-seg and DroneWaste to a waste box head. Steal GIS from LCAS/uav-vineyard-mapping. Optional GRowSeg from HF links-ads/vitigeoss-growseg. Import once into Marcaj with 311 unchanged GeoTIFFs.

## Locked

- Labels: vineyard polygon, waste bbox, row polyline, interrow_area
- One team_upload.zip, original tif names, then publish
- Measurements planar EPSG:32635, no DEM
- Closed walk, start snap <= 5 m, inter-row + passages only

## Hardware

- H100: yolo11m-seg imgsz 1280
- 16 GB: yolo11s-seg imgsz 1024 batch 4, MobileSAM
- CPU emergency: GRowSeg + classical waste

## Sequence

1. Train on public data only. Do not label Siret3 outside Marcaj.
2. Optional: GRowSeg, SAM2, LCAS mapping helpers.
3. Dry-run CVAT 1.1 on 3 tiles, then one 311-file zip, publish.
4. Measure and route from the Marcaj export.
5. MapLibre on port 43173. Freeze Sunday 15:00.
