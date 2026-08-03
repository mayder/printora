from __future__ import annotations


DEFAULT_PERSONAL_STORAGE_QUOTA_BYTES = 1024 * 1024 * 1024


def personal_storage_quota(connection, owner_user_id: int) -> int:
    row = connection.execute(
        """
        SELECT quota_bytes
        FROM social_file_storage_policies
        WHERE status = 'active'
          AND ((scope_type = 'user' AND scope_id = ?) OR scope_type = 'global')
        ORDER BY CASE scope_type WHEN 'user' THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (owner_user_id,),
    ).fetchone()
    return int(row["quota_bytes"]) if row is not None else DEFAULT_PERSONAL_STORAGE_QUOTA_BYTES


def total_personal_storage_used(connection, owner_user_id: int) -> int:
    row = connection.execute(
        """
        SELECT COALESCE(SUM(size_bytes), 0) AS used_bytes FROM (
            SELECT COALESCE(lf.uploaded_size_bytes, lf.size_bytes, 0) AS size_bytes
            FROM social_library_files lf
            JOIN social_library_items li ON li.id = lf.item_id
            WHERE li.owner_user_id = ? AND li.status != 'deleted'
            UNION ALL
            SELECT COALESCE(pf.uploaded_size_bytes, pf.size_bytes, 0) AS size_bytes
            FROM print_project_files pf
            JOIN print_projects pp ON pp.id = pf.project_id
            WHERE pp.owner_user_id = ? AND pp.lifecycle_status != 'archived'
            UNION ALL
            SELECT pc.size_bytes
            FROM photo_capture_photos pc
            JOIN photo_capture_sessions ps ON ps.id = pc.session_id
            WHERE pc.owner_user_id = ? AND ps.status != 'cancelled'
            UNION ALL
            SELECT ra.size_bytes
            FROM photo_reconstruction_artifacts ra
            JOIN photo_reconstruction_jobs rj ON rj.id = ra.reconstruction_job_id
            WHERE rj.owner_user_id = ?
            UNION ALL
            SELECT mr.size_bytes
            FROM mesh_revisions mr
            WHERE mr.owner_user_id = ? AND mr.status = 'succeeded'
              AND NOT EXISTS (
                  SELECT 1 FROM mesh_revision_reviews review
                  WHERE review.revision_id = mr.id
                    AND review.decision = 'approved_for_slicing'
                    AND review.project_file_id IS NOT NULL
              )
        ) usage
        """,
        (owner_user_id, owner_user_id, owner_user_id, owner_user_id, owner_user_id),
    ).fetchone()
    return int(row["used_bytes"] or 0)
