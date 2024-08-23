from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
from bs4 import BeautifulSoup

from blackboard.api_extended import BlackboardExtended
from blackboard.blackboard import BBCourseContent
from blackboard.exceptions import BBBadRequestError

from blackboard.filters import (
    BBAttachmentFilter,
    BBMembershipFilter,
    BWFilter
)

from .attachment import Attachment
from .api_path import BBContentPath
from .attachment_anchors import URLAttachment
from .job import DownloadJob

logger = logging.getLogger(__name__)

class Document:
    """Represents a file with attachments in the Blackboard API"""
    def __init__(self, content: BBCourseContent, api_path: BBContentPath,
                 job: DownloadJob):

        attachments = None
        # This allows us to check if the document uses regular attachments or stores them in the body
        try:
            attachments = job.session.fetch_file_attachments(**api_path)
            assert isinstance(attachments, list)
        except BBBadRequestError:
            logger.error(f"Error fetching attachments for {content.title}")

        self.attachments = []

        if attachments is None:
            # Document contains anchor links to file but not attachments
            soup = BeautifulSoup(content.body, 'html.parser')
            links = soup.find_all('a', href=True)
            if links:
                hrefs = [link['href'] for link in links if link['href'].lower().endswith(".pdf")] # Only download PDFs
                self.attachments = [URLAttachment(href) for href in hrefs]
            return

        att_filter = BBAttachmentFilter(mime_types=BWFilter(['video/*']))
        filtered_attachments = list(att_filter.filter(attachments))


        for i, attachment in enumerate(filtered_attachments):
            self.attachments.append(
                Attachment(attachment, api_path, job)
            )

    def write(self, path: Path, executor: ThreadPoolExecutor):
        # If only attachment, just use parent
        if len(self.attachments) > 1:
            path.mkdir(exist_ok=True, parents=True)
        else:
            path = path.parent

        while "ultraDocumentBody" in path.name: # When downloading from URL, sometimes the directory is wrong
            path = path.parent

        for attachment in self.attachments:
            attachment.write(path, executor)

    @property
    def create_dir(self) -> bool:
        return False