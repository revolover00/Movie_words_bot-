// Only authenticated private-chat recipients can save or report a delivered lesson.
export const lessonAction = kind => ['lesson_save','lesson_clip','lesson_explanation','lesson_show','lesson_known','lesson_repeat'].includes(kind);
export async function applyLessonAction(client, chatId, kind, contentId) {
  if (['lesson_save','lesson_clip','lesson_explanation'].includes(kind)) {
    const sent = await client.query(`SELECT explanation_language FROM delivery_attempts
      WHERE chat_id=$1 AND content_id=$2 AND status='sent' ORDER BY updated_at DESC LIMIT 1`, [chatId, contentId]);
    if (!sent.rows.length) return { kind:'missing' };
    if (kind === 'lesson_save') {
      await client.query(`INSERT INTO saved_lessons(chat_id,content_id,explanation_language)
        VALUES($1,$2,$3) ON CONFLICT(chat_id,content_id) DO NOTHING`, [chatId,contentId,sent.rows[0].explanation_language]);
      return { kind:'saved' };
    }
    await client.query(`INSERT INTO lesson_feedback(chat_id,content_id,reason) VALUES($1,$2,$3)
      ON CONFLICT DO NOTHING`, [chatId,contentId,kind === 'lesson_clip'?'clip':'explanation']);
    return { kind:'reported' };
  }
  if (kind === 'lesson_show') {
    const result = await client.query(`SELECT c.caption FROM saved_lessons s JOIN lesson_captions c
      ON c.content_id=s.content_id AND c.explanation_language=s.explanation_language
      WHERE s.chat_id=$1 AND s.content_id=$2`, [chatId,contentId]);
    return result.rows[0] ? { kind:'show', caption:result.rows[0].caption } : { kind:'missing' };
  }
  const result = await client.query(`UPDATE saved_lessons SET
    next_review_at=now()+make_interval(days=>CASE WHEN $3 THEN LEAST(review_days*2,30) ELSE 1 END),
    review_days=CASE WHEN $3 THEN LEAST(review_days*2,30) ELSE 1 END
    WHERE chat_id=$1 AND content_id=$2 AND next_review_at<=now() RETURNING content_id`, [chatId,contentId,kind==='lesson_known']);
  return { kind:result.rowCount?'reviewed':'missing' };
}
