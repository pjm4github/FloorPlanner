"""Standalone viewers for FloorPlanner documents.

Nothing in here imports `floorplanner` — these read saved v5 JSON directly,
so a viewer cannot affect the editor and needs none of its machinery. It
lives *under* the app package for distribution reasons only (one top-level
name per project); the independence is the point, and a future import of
`floorplanner.*` from here should be argued, not assumed.
"""
