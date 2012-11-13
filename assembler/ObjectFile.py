from collections import namedtuple

ExportEntry = namedtuple('ExportEntry', 'export_symbol addr')
ImportEntry = namedtuple('ImportEntry', 'import_symbol addr')
RelocEntry = namedtuple('RelocEntry', 'reloc_segment addr')

class ObjectFile(object):
	def __init__(self):
		self.name = None
		self.seg_data = {}
		self.export_table = []
		self.import_table = []
		self.reloc_table = []

	@classmethod
	def fromAssembler(cls, seg_data, export_table, import_table, reloc_table):
		obj = cls()
		
		#sanity checks for supplied types
		assert isinstance(seg_data, dict)
		for table in (export_table, import_table, reloc_table):
			assert isinstance(table, list)

		obj.seg_data = seg_data
		obj.export_table = export_table
		obj.import_table = import_table
		obj.reloc_table = reloc_table

		return obj

	def __repr__(self):
		str =  "\nObjectFile:\n"
		str += "\tseg_data: %s\n" % self.seg_data
		str += "\texport_table: %s\n" % self.export_table
		str += "\timport_table: %s\n" % self.import_table
		str += "\treloc_table: %s\n" % self.reloc_table
		return str
