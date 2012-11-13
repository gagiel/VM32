import logging
import struct
from collections import defaultdict

from Exceptions import LinkerError

class Linker(object):
	def __init__(self):
		pass

	def link(self, objectFiles):
		self.objectFiles = objectFiles
		self.logger = logging.getLogger('Linker')

		self.logger.debug("Linker initialized")

		#compute segment map - i.e. where will wich segment be placed at in memory
		self.logger.debug("Creating segment map")
		segment_map, total_size = self._compute_segment_map(objectFiles, 0)
		self.logger.debug("Total occupied memory size is %d bytes" % total_size)
		self.logger.debug("Segment map: %s" % segment_map)

		#gather all exports in the objectFiles
		self.logger.debug("Gathering exports")
		exports = self._collect_exports(self.objectFiles)
		self.logger.debug("Gathered exports: %s" % exports)

		self.logger.debug("Resolving imports")
		self._resolve_imports(objectFiles, exports, segment_map)
		self.logger.debug("Resolved imports")

		self.logger.debug("Resolving relocations")
		self._resolve_relocations(objectFiles, segment_map)
		self.logger.debug("Resolved relocations")

		self.logger.debug("Building executable image")
		image = self._build_memory_image(objectFiles, segment_map, total_size)
		self.logger.debug("Finished buildinng executable image")
		
		return image

	def _build_memory_image(self, object_files, segment_map, total_size):
		SENTINEL = -999
		image = [SENTINEL] * total_size

		for idx, obj in enumerate(object_files):
			for segment in obj.seg_data:
				seg_data = obj.seg_data[segment]

				start = segment_map[idx][segment]
				end = start + len(seg_data)

				for i in range(start, end):
					assert image[i] == SENTINEL, 'segment %s at %d' % (segment, i)

				image[start:end] = seg_data

		for i in range(total_size):
			assert image[i] != SENTINEL, 'at %d' % i

		return image

	def _resolve_relocations(self, object_files, segment_map):
		for idx, obj in enumerate(object_files):
			for reloc_seg, addr in obj.reloc_table:
				if not reloc_seg in segment_map[idx]:
					self._linker_error("Relocation entry in object [%t] refers to unknown segment %s" % (
						self._object_id(obj), reloc_seg))

				mapped_address = segment_map[idx][reloc_seg]

				self._patch_segment_data(obj.seg_data[addr.segment], addr.offset, mapped_address, reloc_seg)

	def _resolve_imports(self, object_files, exports, segment_map):
		for idx, obj in enumerate(object_files):
			import_table = object_files[idx].import_table

			for sym, import_addr in import_table:
				if not sym in exports:
					self._linker_error("Failed import of symbol '%s' at object [%s]" % (
						sym, self._object_id(obj)))
				exp_obj_idx, exp_address = exports[sym]

				mapped_address = segment_map[exp_obj_idx][exp_address.segment]
				mapped_address += exp_address.offset

				#self.logger.debug("Resolving imported symbol '%s' of object [%s] at address %#x to address %#x" % (
				#	sym, self._object_id(obj), mapped_address, exp_address))

				self._patch_segment_data(obj.seg_data[import_addr.segment], import_addr.offset, mapped_address, sym)

	def _patch_segment_data(self, seg_data, instr_offset, mapped_address, name):
		if instr_offset > len(seg_data)-1:
			self._linker_error("Patching (%s) of '%s', bad offset into segment" % (
				type, name))
		seg_data[instr_offset] = struct.pack("<I", mapped_address)

	def _compute_segment_map(self, object_files, offset=0):
		#TODO: replace with linker script later

		#get sizes of each section over all object files
		segment_size = defaultdict(int)
		for obj in object_files:
			for segment in obj.seg_data:
				segment_size[segment] += len(obj.seg_data[segment])

		#get start addresses of each (now combined) segment
		segment_ptr = {}
		ptr = offset

		#put vectors at the beginning for now until we have a linker script
		if "vectors" in segment_size:
			segment_ptr["vectors"] = ptr
			ptr += segment_size["vectors"]

		for segment in sorted(segment_size):
			if segment not in ("vectors"):
				segment_ptr[segment] = ptr
				ptr += segment_size[segment]

		total_size = ptr - offset

		#create a map of all segments and save where the segment of each object
		#fill will end at in memory
		segment_map = []
		for obj in object_files:
			obj_segment_map = {}
			for segment in obj.seg_data:
				obj_segment_map[segment] = segment_ptr[segment]
				segment_ptr[segment] += len(obj.seg_data[segment])
			segment_map.append(obj_segment_map)

		return segment_map, total_size


	def _collect_exports(self, object_files):
		exports = {}

		for idx, obj in enumerate(object_files):
			for export in obj.export_table:
				sym_name = export.export_symbol
				if sym_name in exports:
					other_idx = exports[sym_name][0]
					self._linker_error(
						"Duplicated export symbol '%s' at objects [%s] and [%s]" % (
							sym_name,
							self._object_id(object_files[idx]),
							self._object_id(object_files[other_idx])))

				exports[sym_name] = (idx, export.addr)

		return exports

	def _object_id(self, object_file):
		if object_file.name:
			return object_file.name
		else:
			return hex(id(object_file))

	def _linker_error(self, msg):
		raise LinkerError(msg)
